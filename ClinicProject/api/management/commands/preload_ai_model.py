from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Preload the AI summarization model into memory (useful for warmup)'

    def add_arguments(self, parser):
        parser.add_argument('--model', dest='model', help='Model name to load', default='sshleifer/distilbart-cnn-12-6')

    def handle(self, *args, **options):
        model = options.get('model')
        self.stdout.write(f'Preloading AI model: {model}...')
        try:
            # Import loader from views to warm the model
            from api.views import load_ai_model
            ok = load_ai_model(model)
            if ok:
                self.stdout.write(self.style.SUCCESS('Model loaded successfully.'))
            else:
                self.stdout.write(self.style.ERROR('Model failed to load. Check logs for details.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error while preloading model: {e}'))
