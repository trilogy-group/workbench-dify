import core.moderation.base
from posthog import Posthog

posthog = Posthog(os.environ.get('POSTHOG_PROJECT_KEY'), host="https://us.i.posthog.com")
