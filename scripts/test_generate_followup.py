import traceback
from config import Config
from src.agents.invoice_followup_agent import InvoiceFollowupAgent

if __name__ == '__main__':
    try:
        print('Config:')
        print('  GOOGLE_API_KEY present:', bool(Config.GOOGLE_API_KEY))
        print('  GEMINI_MODEL:', Config.GEMINI_MODEL)
        print('  FREE_TIER_MODE:', Config.FREE_TIER_MODE)
        print('  FREE_TIER_CAP:', Config.FREE_TIER_CAP)

        agent = InvoiceFollowupAgent()
        print('\nRunning generate_batch_followups() (defaults)...')
        results = agent.generate_batch_followups()
        print('\nResults:')
        print(results)

    except Exception as e:
        print('Exception occurred:')
        traceback.print_exc()
