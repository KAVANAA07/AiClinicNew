from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Doctor

# This dictionary maps your Specializations to common symptoms
SPECIALTY_KEYWORDS = {
    "General Physician": "fever cold flu headache cough body pain weakness viral infection sick",
    "Cardiologist": "heart chest pain palpitations breathlessness blood pressure attack pulse",
    "Dermatologist": "skin rash acne itching hair loss pimples allergy face spots",
    "Orthopedic": "bone fracture joint pain knee back pain muscle tear arthritis leg hand",
    "Pediatrician": "child baby infant fever growth vaccination kids crying stomach",
    "Gastroenterologist": "stomach pain gas acidity digestion vomiting loose motion belly",
    "Neurologist": "headache migraine dizziness seizure nerve brain paralysis confusion",
    "Gynecologist": "period pregnancy women menstrual baby delivery pain bleeding",
    "Dentist": "tooth pain teeth gum bleeding cavity mouth jaw",
    "ENT": "ear nose throat pain sinus voice hearing swallowing"
}

def find_best_doctor(symptoms, clinic_id):
    # 1. Get doctors ONLY for the selected clinic
    doctors = Doctor.objects.filter(clinic__id=clinic_id)
    
    if not doctors.exists():
        return None

    # 2. Prepare Data (Mapping Specialization to Keywords)
    doctor_descriptions = []
    
    for doc in doctors:
        # Fetch keywords based on the doctor's specialization
        # If specialization is not in our list, default to just the name
        keywords = SPECIALTY_KEYWORDS.get(doc.specialization, "")
        
        # Combine: "Cardiologist heart chest pain..."
        desc = f"{doc.specialization} {keywords}"
        doctor_descriptions.append(desc)

    # 3. The AI Math (TF-IDF)
    vectorizer = TfidfVectorizer(stop_words='english')
    
    # Combine doctors + patient symptoms
    all_text = doctor_descriptions + [symptoms]
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_text)
        
        # Compare symptoms (last item) against doctors
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
        
        # Find highest score
        best_match_index = cosine_sim.argmax()
        
        # If the match is 0 (no relation at all), return None
        if cosine_sim[0][best_match_index] == 0:
            return None
            
        return doctors[int(best_match_index)]
        
    except ValueError:
        # Handles empty input
        return None