# ClinicProject/api/management/commands/build_patient_index.py
from django.core.management.base import BaseCommand, CommandError

from api.utils.ai_history import build_index_for_patient


class Command(BaseCommand):
    help = "Build or rebuild the AI index (embeddings) for a single patient."

    def add_arguments(self, parser):
        parser.add_argument("--patient_id", type=int, required=True, help="ID of the patient to index")

    def handle(self, *args, **options):
        pid = options.get("patient_id")
        if not pid:
            raise CommandError("Please provide --patient_id")
        self.stdout.write(f"Building index for patient {pid} ...")
        res = build_index_for_patient(pid)
        if res.get("status") == "ok":
            self.stdout.write(self.style.SUCCESS(f"Index built: {res['num_chunks']} chunks saved."))
            self.stdout.write(f"Emb path: {res['emb_path']}")
            self.stdout.write(f"Meta path: {res['meta_path']}")
        else:
            self.stdout.write(self.style.WARNING(f"No data: {res.get('message')}"))
