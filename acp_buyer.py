"""
acp_buyer.py — Trinity Oracle → Trinity Agent 자기결제 루프 v6
────────────────────────────────────────────────────────────────
구조:
  구매자(Buyer)  : Trinity Oracle  (BUYER2_*  환경변수)
  판매자(Seller) : Trinity Agent   (BUYER_AGENT_WALLET_ADDRESS)

ACP 결제 흐름:
1. initiate_job()               — 구매 요청 생성 (온체인)
2. 폴링: TRANSACTION memo 출현  — seller가 accept 후 결제 요청
3. pay_and_accept_requirement() — USDC 결제
4. 폴링: COMPLETED 대기
"""
import os, time, logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.WARNING)

# ── 구매자: Trinity Oracle ──────────────────────────────────────
BUYER_PRIVATE_KEY  = os.getenv("BUYER2_PRIVATE_KEY", "")
BUYER_AGENT_WALLET = os.getenv("BUYER2_AGENT_WALLET_ADDRESS", "")
BUYER_ENTITY_ID    = int(os.getenv("BUYER2_ENTITY_ID", "0"))

# ── 판매자: Trinity Agent (자기 자신) ─────────────────────────────
SELLER_WALLET      = os.getenv("BUYER_AGENT_WALLET_ADDRESS",
                                "0xaC44D4C2De4d3b49844ac4B3500Ab49ad57b2dEB")

DELAY_BETWEEN_JOBS = 30
POLL_INTERVAL      = 5
ACCEPT_TIMEOUT     = 120   # seller accept 대기 (초)
DELIVER_TIMEOUT    = 120   # deliver/complete 대기 (초)

# ── 10회 자기결제 시나리오 (Trinity Oracle → Trinity Agent) ────────
# 총 비용: $0.01×9 + $0.50×1 = $0.59
# Trinity Agent 등록 서비스: dailyLuck / sectorFeed / dailySignal / deepLuck
E2E_SCENARIOS = [
    ("dailyLuck",   0.01, "Self-purchase run 01 - daily luck"),
    ("sectorFeed",  0.01, "Self-purchase run 02 - sector feed"),
    ("dailySignal", 0.01, "Self-purchase run 03 - daily signal"),
    ("dailyLuck",   0.01, "Self-purchase run 04 - daily luck"),
    ("sectorFeed",  0.01, "Self-purchase run 05 - sector feed"),
    ("dailySignal", 0.01, "Self-purchase run 06 - daily signal"),
    ("dailyLuck",   0.01, "Self-purchase run 07 - daily luck"),
    ("sectorFeed",  0.01, "Self-purchase run 08 - sector feed"),
    ("dailyLuck",   0.01, "Self-purchase run 09 - daily luck"),
    ("deepLuck",    0.50, "Self-purchase run 10 - premium deep luck"),
]
DEEPLUCK_PARAMS = {"birth_date": "2025-01-20", "birth_time": "12:00"}

PHASE_TRANSACTION = 2
PHASE_COMPLETED   = 4
PHASE_REJECTED    = 5


def poll_job(buyer_client, job_id, condition_fn, timeout, label):
    """조건 함수가 True를 반환할 때까지 폴링. 타임아웃 시 None 반환"""
    print(f"[Pay] ⏳ {label} (Job {job_id})...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            job = buyer_client.get_job_by_onchain_id(job_id)
            result = condition_fn(job)
            if result is not None:
                return result
        except Exception as e:
            print(f"[Pay] ❗ 폴링 오류: {e}")
        time.sleep(POLL_INTERVAL)
    print(f"[Pay] ⏰ 타임아웃: {label}")
    return None


def _wait_for_transaction_memo(job):
    """TRANSACTION memo(next_phase=2) 존재하면 job 반환, 거절/완료면 False"""
    phase = int(job.phase)
    if phase in (PHASE_COMPLETED, PHASE_REJECTED):
        return False
    if any(int(m.next_phase) == PHASE_TRANSACTION for m in job.memos):
        return job
    return None


def _wait_for_completed(job):
    phase = int(job.phase)
    if phase == PHASE_COMPLETED:
        return True
    if phase == PHASE_REJECTED:
        return False
    return None


def run_e2e_test():
    if not BUYER_PRIVATE_KEY or not BUYER_AGENT_WALLET or not BUYER_ENTITY_ID:
        print("⚠️  BUYER2_* 환경변수를 설정하세요!"); return

    from virtuals_acp.client import VirtualsACP
    from virtuals_acp.contract_clients.contract_client_v2 import ACPContractClientV2
    from virtuals_acp.configs.configs import BASE_MAINNET_ACP_X402_CONFIG_V2
    from virtuals_acp.fare import Fare, FareAmount

    config = BASE_MAINNET_ACP_X402_CONFIG_V2
    fare   = Fare(config.base_fare.contract_address, config.base_fare.decimals)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🔄 Trinity 자기결제 루프 v6                                  ║
╠══════════════════════════════════════════════════════════════╣
║  구매자(Oracle) : {BUYER_AGENT_WALLET[:18]}...
║  판매자(Agent)  : {SELLER_WALLET[:18]}...
║  시나리오       : {len(E2E_SCENARIOS)}회 / 예상비용: $0.59
╚══════════════════════════════════════════════════════════════╝
    """)

    buyer_client = VirtualsACP(
        acp_contract_clients=ACPContractClientV2(
            wallet_private_key=BUYER_PRIVATE_KEY,
            agent_wallet_address=BUYER_AGENT_WALLET,
            entity_id=BUYER_ENTITY_ID,
            config=config,
        ),
        on_evaluate=lambda job: _auto_evaluate(job),
    )

    results = []

    for idx, (service, amount_raw, description) in enumerate(E2E_SCENARIOS, 1):
        print(f"\n[E2E] ── {idx:02d}/{len(E2E_SCENARIOS)} · {service} · ${amount_raw:.2f} ──")

        try:
            # ① Job 생성 (Trinity Oracle → Trinity Agent 자기결제)
            extra = DEEPLUCK_PARAMS if service == "deepLuck" else {}
            job_id = buyer_client.initiate_job(
                provider_address=SELLER_WALLET,
                service_requirement={"service_name": service, "instruction": description,
                                     "test_scenario": f"SELF-{idx:02d}", **extra},
                fare_amount=FareAmount(amount_raw, fare),
                evaluator_address=SELLER_WALLET,   # seller가 직접 deliver+evaluate
            )
            print(f"[E2E] 📋 Job={job_id}")

            # ② seller accept + create_payable_requirement() 대기 (TRANSACTION memo 출현)
            accepted_job = poll_job(
                buyer_client, job_id,
                _wait_for_transaction_memo,
                ACCEPT_TIMEOUT,
                "TRANSACTION memo 대기"
            )
            if not accepted_job:
                results.append({"idx": idx, "status": "ACCEPT_TIMEOUT"}); continue

            # ③ 결제 — pay_and_accept_requirement(): TRANSACTION memo 서명 + x402
            print(f"[Pay] 💳 pay_and_accept_requirement() (Job {job_id})")
            try:
                accepted_job.pay_and_accept_requirement("E2E test payment")
                print(f"[Pay] ✅ pay_and_accept_requirement 완료 (Job {job_id})")
            except Exception as e:
                print(f"[Pay] ❌ 결제 실패: {e}")
                results.append({"idx": idx, "status": f"PAY_FAIL:{e}"}); continue

            # ③-b SKIP — seller의 on_evaluate()가 EVALUATION memo + deliver + evaluate 처리
            # buyer가 직접 서명하면 Already signed / AA25 nonce 충돌 발생
            print(f"[Pay] ✅ 결제 완료 → seller가 deliver/evaluate 처리 대기 중...")

            # ④ COMPLETED 대기

            completed = poll_job(
                buyer_client, job_id,
                _wait_for_completed,
                DELIVER_TIMEOUT,
                "COMPLETED 대기"
            )
            status = "COMPLETED" if completed else "TIMEOUT"
            results.append({"idx": idx, "service": service, "job_id": job_id, "status": status})
            print(f"[E2E] {'✅' if completed else '❌'} Job {job_id}: {status}")

        except Exception as e:
            print(f"[E2E] ❌: {e}")
            results.append({"idx": idx, "service": service, "status": f"ERR:{e}"})

        if idx < len(E2E_SCENARIOS):
            print(f"[E2E] ⏳ {DELAY_BETWEEN_JOBS}초 대기...")
            time.sleep(DELAY_BETWEEN_JOBS)

    done = [r for r in results if r.get("status") == "COMPLETED"]
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  📊 결과: ✅ {len(done):2d}회 완료 / ❌ {len(results)-len(done):2d}회 실패
╚══════════════════════════════════════════════════════════════╝""")
    for r in results:
        icon = "✅" if r["status"] == "COMPLETED" else "❌"
        print(f"  {icon} #{r['idx']:02d} {r.get('service','?')}: {r['status']}")
    if len(done) >= 10:
        print("\n🎉 졸업 요건 달성! 대시보드에서 'Graduate Agent' 버튼을 확인하세요!")
    else:
        print(f"\n⚠️  {10 - len(done)}회 더 필요합니다.")


def _auto_evaluate(job):
    try:
        print(f"[Eval] 평가 (Job={job.id})")
        job.evaluate(True, "E2E test: verified")
        print(f"[Eval] ✅")
    except Exception as e:
        print(f"[Eval] ❌: {e}")


if __name__ == "__main__":
    run_e2e_test()
