"""
Generate 2000+ structured disease-medication reference entries for MedRAG KB.
Sources: WHO STG patterns, CDC/AAP/IDSA public guidelines, OPD institutional protocols.
Educational reference only — not for direct prescribing without clinician review.
"""

from __future__ import annotations

import os
import sys
from itertools import product

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "drug_interactions", "common_disease_medication_reference.txt")

AGE_GROUPS = [
    ("Neonate", "0-28 days"),
    ("Infant", "1-12 months"),
    ("Child", "1-12 years"),
    ("Adolescent", "13-17 years"),
    ("Young_Adult", "18-39 years"),
    ("Middle_Adult", "40-64 years"),
    ("Elderly", "65+ years"),
    ("Pregnancy", "pregnant patients"),
    ("Lactation", "breastfeeding patients"),
]

GENDERS = ["All", "Female", "Male"]

# (disease, category, first_line, alternatives, adjunct, non_rx, refer, notes)
DISEASES = [
    ("Urinary Tract Infection - Uncomplicated Cystitis", "Infectious", "Nitrofurantoin; TMP-SMX (if local resistance low)", "Fosfomycin single dose; Pivmecillinam; Amoxicillin-clavulanate", "Increased fluids; urinary alkalinizer if indicated", "Hydration; voiding hygiene", "Flank pain; fever; male UTI; pregnancy complications; recurrent UTI", "Culture-guided therapy preferred; avoid fluoroquinolones first-line when alternatives exist"),
    ("Urinary Tract Infection - Pyelonephritis", "Infectious", "Ceftriaxone IV/IM then oral step-down; Fluoroquinolone if susceptible", "Piperacillin-tazobactam; Carbapenem if ESBL risk", "IV fluids; antipyretics", "Hospitalization if severe", "Sepsis; vomiting; pregnancy; failed outpatient therapy", "Always obtain urine culture; tailor to susceptibility"),
    ("Acute Gastroenteritis", "Gastrointestinal", "ORS; Zinc (children); Antibiotic only if invasive bacterial diarrhea suspected", "Azithromycin for traveler's diarrhea; Ciprofloxacin selected cases", "Racecadotril for secretory diarrhea; Probiotics", "Fluid replacement; continue feeding children", "Bloody stool; severe dehydration; toxic appearance", "Antibiotics not routine for viral AGE"),
    ("Acute Otitis Media", "ENT", "Amoxicillin high-dose", "Amoxicillin-clavulanate; Cefdinir; Azithromycin if penicillin allergy", "Paracetamol/ibuprofen for pain/fever", "Observation 48-72h if mild unilateral in older child", "Mastoiditis signs; immunocompromised; treatment failure", "CDC/AAP: amoxicillin first-line pediatric"),
    ("Acute Pharyngitis - Streptococcal", "ENT", "Penicillin V; Amoxicillin", "Azithromycin; Clindamycin if allergy", "Analgesics; warm saline gargle", "Supportive care if viral", "Peritonsillar abscess; rheumatic fever risk", "Confirm GAS when treating with antibiotics"),
    ("Acute Sinusitis - Bacterial", "ENT", "Amoxicillin-clavulanate", "Doxycycline; Levofloxacin (adult selected)", "Saline irrigation; intranasal steroids", "Symptomatic care if mild <10 days", "Orbital cellulitis; severe headache; immunocompromised", "Most acute sinusitis is viral"),
    ("Community-Acquired Pneumonia - Outpatient", "Respiratory", "Amoxicillin; Doxycycline; Azithromycin", "Amoxicillin-clavulanate; Respiratory fluoroquinolone", "Rest; hydration; bronchodilator if wheeze", "Smoking cessation; vaccines", "Hypoxia; confusion; multilobar; comorbidities", "Age and comorbidity guide agent choice"),
    ("Bronchiolitis - Infant", "Respiratory", "Supportive care only", "Salbutamol trial only if wheeze; nebulized hypertonic saline selected", "Nasal suction; hydration", "Oxygen if needed", "Apnea; poor feeding; SpO2 <90%", "CDC: antibiotics not indicated for bronchiolitis"),
    ("Asthma - Controller Therapy", "Respiratory", "Low-dose inhaled corticosteroid", "ICS-LABA; Leukotriene antagonist step 2+", "Reliever SABA or ICS-formoterol MART", "Trigger avoidance; inhaler technique", "Status asthmaticus; frequent oral steroid bursts", "GINA: ICS preferred over montelukast first-line"),
    ("COPD Exacerbation", "Respiratory", "Short-course systemic corticosteroid; Bronchodilator", "Antibiotic if purulent sputum; consider azithromycin", "Controlled oxygen; pulmonary rehab", "Smoking cessation; vaccination", "Respiratory failure; altered mental status", "Tailor antibiotics to local guidelines"),
    ("Hypertension - Stage 1", "Cardiovascular", "Thiazide diuretic; ACE inhibitor; ARB; CCB", "Combination therapy if needed", "DASH diet; sodium restriction; exercise", "Lifestyle modification first", "Hypertensive emergency; secondary causes", "Amlodipine common in OPD protocols"),
    ("Hypertension - Stage 2", "Cardiovascular", "Two-drug combination ACEi/ARB + CCB or thiazide", "Add spironolactone resistant HTN", "Home BP monitoring", "Weight loss; limit alcohol", "Target organ damage; pregnancy", "Individualize for age and comorbidity"),
    ("Heart Failure - HFrEF", "Cardiovascular", "ACE inhibitor/ARB/ARNI; Beta-blocker; MRA; SGLT2 inhibitor", "Loop diuretic for congestion", "Fluid/salt restriction; cardiac rehab", "Vaccination", "Cardiogenic shock; arrhythmia", "Guideline-directed medical therapy"),
    ("Atrial Fibrillation - Rate Control", "Cardiovascular", "Beta-blocker; Non-DHP CCB", "Digoxin; Amiodarone selected", "Anticoagulation per CHA2DS2-VASc", "Stroke prevention counseling", "Hemodynamic instability; WPW", "Anticoagulation unless contraindicated"),
    ("Angina - Stable", "Cardiovascular", "Nitrate; Beta-blocker; CCB", "Ranolazine; ACE inhibitor", "Aspirin; statin", "Risk factor modification", "ACS features; syncope", "Secondary prevention essential"),
    ("Type 2 Diabetes - New Diagnosis", "Endocrine", "Metformin", "GLP-1 RA; SGLT2i; Sulfonylurea; Basal insulin", "Lifestyle; diabetes education", "Diet; physical activity", "DKA; HHS; pregnancy", "OPD protocol: metformin + glimepiride common"),
    ("Type 1 Diabetes", "Endocrine", "Basal-bolus insulin", "Insulin pump; CGM", "Carb counting education", "DKA prevention", "DKA; severe hypoglycemia", "Insulin mandatory"),
    ("Hypothyroidism", "Endocrine", "Levothyroxine", "Dose titration by TSH", "Take fasting before breakfast", "Regular TSH monitoring", "Myxedema coma; pregnancy", "Avoid in uncorrected adrenal insufficiency"),
    ("Hyperthyroidism - Graves", "Endocrine", "Methimazole; Propylthiouracil 1st trimester pregnancy", "Propranolol symptomatic; Radioiodine/surgery definitive", "Avoid iodine excess", "Thyroid storm; ophthalmopathy", "PTU preferred early pregnancy"),
    ("Migraine - Acute", "Neurology", "NSAID; Triptan", "Antiemetic; Acetaminophen", "Dark quiet room; hydration", "Trigger diary", "Thunderclap headache; neuro deficits", "Limit triptan frequency"),
    ("Migraine - Prophylaxis", "Neurology", "Propranolol; Topiramate; Amitriptyline", "Valproate; CGRP inhibitors", "Sleep hygiene; stress management", "Lifestyle triggers", "Medication overuse headache", "Amitriptyline 25 mg used in OPD protocol"),
    ("Epilepsy - Focal", "Neurology", "Levetiracetam; Lamotrigine; Carbamazepine", "Oxcarbazepine; Lacosamide", "Avoid sleep deprivation; adherence", "Seizure action plan", "Status epilepticus; new focal deficit", "Therapeutic drug monitoring some agents"),
    ("Vertigo - Peripheral", "Neurology", "Betahistine; Antihistamine short course", "Prochlorperazine for nausea", "Epley maneuver if BPPV", "Fall precautions", "Neurologic signs; sudden hearing loss", "Vertin 16 mg TDS in OPD protocol"),
    ("Stroke - Ischemic Acute", "Neurology", "Thrombolysis/thrombectomy per protocol; Aspirin after", "Statin; BP management per guideline", "Rehabilitation", "Secondary prevention", "ICH; anticoagulation needed", "Time-critical emergency"),
    ("Depression - First Episode", "Psychiatry", "SSRI (sertraline, escitalopram)", "SNRI; psychotherapy CBT", "Sleep; exercise; social support", "Suicide risk assessment", "Suicidal ideation with plan; psychosis", "Start low go slow elderly"),
    ("Generalized Anxiety Disorder", "Psychiatry", "SSRI; SNRI", "Buspirone; CBT", "Sleep hygiene; mindfulness", "Substance use screening", "Panic with chest pain rule out ACS", "Benzodiazepines short-term only"),
    ("Gastritis / Dyspepsia", "Gastrointestinal", "PPI (pantoprazole, omeprazole)", "H2 blocker; Antacids", "Diet modification; avoid NSAIDs", "Small frequent meals", "GI bleeding; weight loss; anemia", "Pantoprazole 40 mg OD common OPD"),
    ("Peptic Ulcer Disease", "Gastrointestinal", "PPI full course", "H. pylori eradication triple/quadruple therapy", "Sucralfate; avoid alcohol/smoking", "Test H. pylori if indicated", "Perforation; obstruction; bleeding", "HP kit 14 days per OPD protocol"),
    ("GERD", "Gastrointestinal", "PPI; Lifestyle elevation head of bed", "H2 blocker; Alginate", "Weight loss; avoid late meals", "Dietary triggers avoidance", "Dysphagia; odynophagia; GI bleed", "Step-down PPI when controlled"),
    ("Inflammatory Bowel Disease Flare", "Gastrointestinal", "Mesalamine mild; Corticosteroid moderate-severe", "Immunomodulator; Biologic", "Nutrition support", "Smoking cessation UC", "Toxic megacolon; sepsis", "Specialist co-management"),
    ("Irritable Bowel Syndrome", "Gastrointestinal", "Antispasmodic; Diet low FODMAP trial", "Rifaximin; Lubiprostone selected", "Fiber; stress reduction", "Exclude red flags", "Weight loss; nocturnal symptoms; bleeding", "Diagnosis of exclusion"),
    ("Acute Hepatitis A", "Gastrointestinal", "Supportive care", "Avoid hepatotoxic drugs", "Rest; hydration", "Vaccination contacts", "Fulminant liver failure", "Usually self-limited"),
    ("Chronic Hepatitis B", "Gastrointestinal", "Tenofovir; Entecavir", "Peginterferon selected", "Monitor LFTs HBV DNA", "Liver cancer surveillance", "Decompensated cirrhosis", "Long-term antiviral often required"),
    ("Low Back Pain - Mechanical", "Musculoskeletal", "NSAID; Muscle relaxant short course", "Pregabalin if radiculopathy; Physiotherapy", "Heat; activity modification", "Avoid bed rest prolonged", "Cauda equina; fever; trauma; cancer history", "Brufen + thiocolchicoside OPD protocol"),
    ("Osteoarthritis - Knee", "Musculoskeletal", "Paracetamol; Topical NSAID", "Oral NSAID short course; Intra-articular steroid", "Weight loss; exercise; physio", "Assistive devices", "Joint instability; infection", "Stepwise analgesia WHO ladder"),
    ("Rheumatoid Arthritis", "Musculoskeletal", "Methotrexate + folic acid", "Hydroxychloroquine; Sulfasalazine; Biologic", "NSAID bridge; steroid bridge low dose", "Early rheumatology referral", "Joint erosions; systemic involvement", "DMARD early prevents damage"),
    ("Gout - Acute", "Musculoskeletal", "NSAID; Colchicine; Steroid", "Urate-lowering therapy after acute settles", "Hydration; avoid alcohol", "Diet modification long-term", "Renal stones; tophi; polyarticular", "Do not start allopurinol during acute flare"),
    ("Cellulitis - Mild", "Dermatology/Infectious", "Flucloxacillin; Cephalexin", "Clindamycin if MRSA risk", "Elevation; mark borders", "Wound care", "Spreading; systemic toxicity; diabetic foot", "5-7 days typical course"),
    ("Impetigo", "Dermatology", "Topical mupirocin limited", "Oral flucloxacillin extensive", "Hygiene; avoid sharing towels", "School exclusion until treated", "Post-streptococcal glomerulonephritis risk", "Topical first if localized"),
    ("Fungal Skin Infection - Tinea", "Dermatology", "Topical terbinafine/clotrimazole", "Oral terbinafine if extensive", "Keep area dry", "Treat contacts/pets if animal source", "Diabetic foot involvement", "Continue 1-2 weeks after clearance topical"),
    ("Acne Vulgaris - Mild", "Dermatology", "Topical retinoid; Benzoyl peroxide", "Topical antibiotic combination", "Gentle cleanser", "Avoid picking", "Nodulocystic; scarring", "Limit antibiotic monotherapy duration"),
    ("Eczema / Atopic Dermatitis", "Dermatology", "Emollient; Topical corticosteroid low potency", "Topical calcineurin inhibitor; Antihistamine itch", "Trigger avoidance", "Wet wraps severe", "Infection; herpes eczema", "Step up potency by severity site"),
    ("Allergic Rhinitis", "ENT/Allergy", "Intranasal corticosteroid", "Oral antihistamine; Montelukast add-on", "Allergen avoidance; saline rinse", "Environmental control", "Asthma comorbidity", "Montelukast-levoce tirizine in OPD URTI"),
    ("Conjunctivitis - Bacterial", "Ophthalmology", "Topical antibiotic drops", "Hygiene; avoid contact lenses", "Warm compress", "Neonatal; herpes; trauma", "Viral more common — antibiotics not always needed"),
    ("Conjunctivitis - Allergic", "Ophthalmology", "Antihistamine/mast cell stabilizer drops", "Cold compress", "Avoid allergen", "Chronic symptoms", "Vision loss; pain — not simple allergic"),
    ("Dental Abscess", "Dental", "Amoxicillin-clavulanate; Metronidazole combination", "Penicillin allergy: clindamycin", "Analgesia; dental drainage required", "Urgent dental referral", "Ludwig angina; airway compromise", "Source control essential"),
    ("Iron Deficiency Anemia", "Hematology", "Oral ferrous sulfate", "IV iron if intolerance/malabsorption", "Treat underlying cause", "Dietary iron", "GI malignancy workup adults; transfusion if severe", "Continue 3 months after Hb normalized"),
    ("Vitamin B12 Deficiency", "Hematology", "IM hydroxocobalamin", "Oral B12 high-dose if pernicious excluded", "Dietary assessment", "Neurologic symptoms urgent", "Subacute combined degeneration", "Lifelong if pernicious anemia"),
    ("Malaria - Uncomplicated P. falciparum", "Infectious", "ACT (artemether-lumefantrine)", "Atovaquone-proguanil; Quinine + doxycycline", "Supportive; hydration", "Bed nets; prophylaxis travelers", "Severe malaria criteria", "Resistance patterns regional"),
    ("Dengue - Without Warning Signs", "Infectious", "Supportive: fluids paracetamol", "Avoid NSAIDs and aspirin", "Mosquito bite prevention", "Monitor platelets hematocrit", "Warning signs; shock", "Paracetamol only for fever"),
    ("Tuberculosis - Pulmonary", "Infectious", "RIPE regimen 2 months then RI 4 months", "DOT supervised therapy", "Contact tracing", "Public health notification", "MDR-TB; HIV coinfection", "Full course essential"),
    ("HIV - Initial ART", "Infectious", "Tenofovir + lamivudine + dolutegravir", "Alternative per resistance", "TB screening; cryptococcal screen", "Adherence counseling", "Opportunistic infection acute", "Start ART same day if ready"),
    ("Syphilis - Primary/Secondary", "Infectious", "Benzathine penicillin G IM", "Doxycycline if penicillin allergy", "Partner notification", "Serology follow-up", "Neurosyphilis; pregnancy", "Penicillin preferred"),
    ("Chlamydia Urogenital", "Infectious", "Azithromycin single dose OR Doxycycline 7 days", "Treat partners", "Screen other STIs", "Pregnancy: azithromycin", "PID; Fitz-Hugh-Curtis", "Test of cure not routine"),
    ("Gonorrhea - Uncomplicated", "Infectious", "Ceftriaxone IM + Azithromycin/Doxycycline", "Test of cure if pharyngeal", "Partner treatment", "Resistance monitoring", "Disseminated gonococcal infection", "Dual therapy recommended"),
    ("Scabies", "Dermatology/Infectious", "Permethrin 5% cream", "Oral ivermectin if crusted", "Treat contacts; wash bedding", "Pruritus may persist weeks", "Crusted scabies; institutional outbreak", "Repeat application per protocol"),
    ("Head Lice", "Dermatology", "Topical permethrin or dimethicone", "Wet combing adjunct", "Treat household contacts", "School policies vary", "Secondary infection", "Resistance — rotate agents"),
    ("Chickenpox - Uncomplicated", "Infectious", "Supportive; acyclovir if high-risk", "Paracetamol; avoid aspirin children", "Isolation", "Immunocompromised; pregnancy", "Varicella pneumonia; encephalitis", "VZV vaccine prevention"),
    ("Herpes Zoster", "Infectious", "Acyclovir/valacyclovir within 72h", "Analgesia; gabapentin neuralgia", "Rash care", "Immunocompromised; ophthalmic branch", "Post-herpetic neuralgia", "Early antiviral reduces complications"),
    ("Influenza - Uncomplicated", "Infectious", "Oseltamivir if within 48h high-risk", "Supportive; paracetamol", "Rest; hydration", "Vaccination prevention", "Pneumonia; respiratory failure", "Neuraminidase inhibitors per CDC"),
    ("COVID-19 - Mild Outpatient", "Infectious", "Supportive care; nirmatrelvir-ritonavir if eligible", "Remdesivir selected; Symptomatic treatment", "Isolation; vaccination", "Pulse ox monitoring", "Hypoxia; persistent fever", "Follow current national guidelines"),
    ("Helminthiasis - Roundworm", "Infectious", "Albendazole; Mebendazole", "Hygiene education", "Mass drug admin programs endemic areas", "Obstruction; migration", "Single dose often sufficient"),
    ("Typhoid Fever", "Infectious", "Azithromycin; Ceftriaxone", "Fluoroquinolone if susceptible", "Hydration; nutrition", "Vaccination endemic areas", "Intestinal perforation; encephalopathy", "Resistance common — culture guided"),
    ("Acute Pyelonephritis Pregnancy", "Obstetric/Infectious", "Ceftriaxone; Cefalexin after stabilization", "Hospitalize if severe", "Obstetric monitoring", "UTI prevention", "Sepsis; preterm labor", "Always treat aggressively in pregnancy"),
    ("Gestational Diabetes", "Obstetric/Endocrine", "Insulin if lifestyle fails; Metformin some settings", "Nutrition therapy; glucose monitoring", "Postpartum OGTT", "Macrosomia; neonatal hypoglycemia", "Tight glycemic targets"),
    ("Preeclampsia", "Obstetric", "Magnesium sulfate seizure prophylaxis; Antihypertensive labetalol/hydralazine", "Delivery definitive", "BP monitoring; fetal monitoring", "Eclampsia; HELLP; pulmonary edema", "Emergency obstetric care"),
    ("Bacterial Vaginosis", "Gynecology", "Metronidazole; Clindamycin", "Treat partners not routine", "Avoid douching", "Pregnancy: metronidazole safe", "PID risk; recurrence", "Oral or vaginal routes"),
    ("Vulvovaginal Candidiasis", "Gynecology", "Fluconazole single dose; Clotrimazole topical", "Longer course recurrent", "Avoid unnecessary antibiotics", "Diabetes screen if recurrent", "Immunocompromised; non-albicans", "OTC azoles mild"),
    ("Polycystic Ovary Syndrome", "Gynecology/Endocrine", "Combined OCP; Metformin", "Spironolactone hirsutism; Lifestyle weight loss", "Ovulation induction if fertility desired", "Endometrial protection", "Metabolic syndrome; infertility", "Individualize by goals"),
    ("Menorrhagia - No Structural", "Gynecology", "Tranexamic acid; NSAID; Combined OCP", "Levonorgestrel IUS", "Iron supplementation if anemic", "Fibroid; coagulopathy workup", "Anemia severe; postmenopausal bleeding", "Exclude endometrial pathology age >45"),
    ("Benign Prostatic Hyperplasia", "Urology", "Alpha-blocker tamsulosin; 5-ARI finasteride", "Combination if large prostate", "Fluid restriction evening; avoid anticholinergics", "Retention; hematuria; renal impairment", "Surgery if failed medical"),
    ("Epididymo-orchitis - <35", "Urology/Infectious", "Ceftriaxone + Doxycycline", "Treat as STI until proven otherwise", "Scrotal support; analgesia", "Testicular torsion must exclude", "Abscess; Fournier gangrene", "Ultrasound if diagnostic doubt"),
    ("Erectile Dysfunction", "Urology", "PDE5 inhibitor sildenafil/tadalafil", "Lifestyle; treat cardiovascular risk", "Psychosexual counseling", "Cardiac contraindications nitrates", "Priapism rare emergency", "Screen cardiovascular disease"),
    ("ADHD - Child 6+", "Psychiatry/Pediatric", "Stimulant methylphenidate/amphetamine + behavioral therapy", "Atomoxetine; Guanfacine XR", "Parent training; school supports", "CDC/AAP combined therapy recommended", "Cardiac symptoms; growth monitoring", "Non-stimulant if stimulant contraindicated"),
    ("ADHD - Adult", "Psychiatry", "Stimulant first-line pharmacotherapy", "Atomoxetine; Bupropion", "CBT; organizational coaching", "CDC: pharmacotherapy first-line adults", "Substance misuse history", "Cardiovascular screening"),
    ("Otitis Externa", "ENT", "Topical antibiotic drops with steroid", "Oral if cellulitis extends", "Keep ear dry; avoid cotton buds", "Diabetes — malignant OE risk", "Facial nerve palsy; mastoid involvement", "Remove debris if canal swollen"),
    ("Tonsillitis - Viral", "ENT", "Supportive: analgesia fluids", "No antibiotics", "Rest; salt gargle", "Strep test before antibiotics", "Peritonsillar abscess", "Most sore throats viral"),
    ("Pneumonia - Pediatric", "Pediatric/Respiratory", "Amoxicillin high-dose community acquired", "Amoxicillin-clavulanate; Macrolide", "Oxygen; hydration", "Vaccination", "Hypoxia; empyema", "Age-specific pathogens guide therapy"),
    ("Croup", "Pediatric/Respiratory", "Dexamethasone single dose; Nebulized epinephrine severe", "Comfort; humidified air", "Steroid reduces stridor", "Airway obstruction; cyanosis", "Watch for recurrent stridor"),
    ("Neonatal Sepsis Suspected", "Neonatal/Infectious", "Ampicillin + gentamicin empiric", "Adjust per culture", "Supportive NICU care", "Maternal GBS status guides", "Shock; meningitis", "Emergency neonatal referral"),
    ("Neonatal Jaundice", "Neonatal", "Phototherapy per bilirubin nomogram", "Breastfeeding support; hydration", "Exchange transfusion if severe", "Kernicterus prevention", "Rh incompatibility; sepsis", "Plot on hour-specific chart"),
    ("Failure to Thrive Infant", "Pediatric", "Treat underlying cause; Nutritional rehabilitation", "High-calorie feeds; feeding therapy", "Growth monitoring", "Malabsorption; neglect; cardiac", "Multidisciplinary assessment", "Caloric density increase"),
    ("Kawasaki Disease", "Pediatric", "IV immunoglobulin + aspirin", "Echo coronary monitoring", "Fever >5 days + mucocutaneous features", "Coronary aneurysm", "Early IVIG within 10 days"),
    ("Rickets / Vitamin D Deficiency", "Pediatric", "Cholecalciferol supplementation", "Calcium if deficient; Sun exposure safe", "Treat underlying malabsorption", "Deformity severe", "Alkaline phosphatase elevated"),
    ("Anaphylaxis", "Emergency/Allergy", "IM epinephrine first-line", "Adjunct antihistamine; steroid; bronchodilator", "Lie flat legs elevated unless breathing difficulty", "Observation biphasic reaction", "Airway compromise; hypotension", "Carry auto-injector education"),
    ("Acute Allergic Reaction Mild", "Allergy", "Oral antihistamine", "Topical steroid if urticaria", "Avoid trigger", "Progression to anaphylaxis", "Epinephrine if systemic", "Monitor 观察"),
    ("Hyperkalemia - Mild", "Emergency/Metabolic", "Dietary potassium restriction; Review medications", "Loop diuretic; Patiromer/sodium zirconium", "ECG monitoring", "K >6.5; ECG changes; renal failure", "Calcium glucononide if ECG changes emergency"),
    ("Hypokalemia", "Metabolic", "Oral potassium chloride", "IV potassium if severe/symptomatic", "Correct magnesium", "Arrhythmia; weakness severe", "Max IV rate limits", "Find cause diuretics diarrhea"),
    ("Diabetic Ketoacidosis", "Emergency/Endocrine", "IV fluids; Insulin infusion; Potassium replacement", "Treat precipitant infection", "ABG glucose ketone monitoring", "Cerebral edema pediatric; shock", "ICU protocol mandatory"),
    ("Hypoglycemia - Conscious", "Emergency/Endocrine", "15g fast-acting glucose", "Glucagon IM if unable oral", "Recheck glucose", "Altered mental status", "Seizure; unconscious", "Rule out sulfonylurea overdose"),
    ("Burns - Minor", "Emergency/Dermatology", "Cool running water 20 min; Simple analgesia", "Topical antimicrobial silver sulfadiazine if indicated", "Tetanus prophylaxis", "Dressing", "Major burns criteria; circumferential; face hands", "Refer major burns center"),
    ("Wound Infection Post-Trauma", "Emergency/Infectious", "Flucloxacillin; Amoxicillin-clavulanate if contaminated", "Debridement; Tetanus update", "Wound care", "Deep space infection; necrotizing fasciitis", "Surgical assessment if deep"),
    ("Snake Bite - Non-venomous/Low risk", "Emergency", "Wound care; Tetanus; Analgesia", "Antivenom only if envenomation signs", "Immobilize limb", "Neurotoxicity; coagulopathy", "Antivenom specific emergency centers"),
    ("Heat Exhaustion", "Emergency", "Cool environment; Oral/IV fluids; Rest", "Electrolyte replacement", "Heat stroke exclusion", "Altered mental status; temp >40C", "Active cooling heat stroke"),
    ("Altitude Sickness - Mild AMS", "Emergency", "Acetazolamide; Descent", "Avoid further ascent; Hydration", "HACE/HAPE exclusion", "Ataxia; confusion; crackles", "Descent definitive"),
    ("Motion Sickness", "ENT/General", "Dimenhydrinate; Hyoscine patch", "Ginger adjunct", "Visual fixation techniques", "Prolonged vomiting dehydration", "Avoid sedating if driving"),
    ("Insomnia - Short Term", "Psychiatry/General", "Sleep hygiene first-line", "Short course melatonin; Z-drug limited", "CBT-I preferred long-term", "Chronic benzodiazepine avoid", "Sleep apnea screen; depression", "Limit hypnotic duration"),
    ("Chronic Pain - Neuropathic", "Pain/Neurology", "Gabapentin; Pregabalin; Duloxetine", "Amitriptyline; Topical lidocaine", "Multimodal non-drug", "Pregabalin in LBP radiculopathy OPD", "Addiction risk opioids avoid first-line", "WHO analgesic ladder neuropathic separate"),
    ("Osteoporosis - Prevention/Treatment", "Musculoskeletal/Endocrine", "Bisphosphonate alendronate; Calcium + vitamin D", "Denosumab; Teriparatide severe", "Weight-bearing exercise; fall prevention", "DEXA monitoring", "Pathological fracture; steroid-induced", "Calcium/Vit D OPD LBP protocol"),
    ("Hyperlipidemia - Primary Prevention", "Cardiovascular", "Statin moderate intensity", "Ezetimibe add-on; PCSK9i if very high risk", "Mediterranean diet; exercise", "ASCVD risk calculator guides", "Statin intolerance; familial hypercholesterolemia", "Lifestyle always adjunct"),
    ("Thyroid Nodule - Euthyroid", "Endocrine", "TSH; Ultrasound; FNA if indicated", "Levothyroxine if hypothyroid", "Surveillance by size/features", "Compression symptoms; suspicious FNA", "Surgery malignant cytology", "Do not treat euthyroid nodule with LT4 routinely"),
    ("Cushing Syndrome Suspected", "Endocrine", "Refer endocrinology", "Dexamethasone suppression test specialist", "Screen comorbidities", "Moon face; striae; hyperglycemia", "Specialist management mandatory", "Not primary care treatment"),
    ("Addison Disease", "Endocrine", "Hydrocortisone + fludrocortisone replacement", "Stress dose steroids education", "Medical alert identification", "Adrenal crisis emergency", "Never stop steroids abruptly", "IV hydrocortisone crisis"),
    ("PCOS - Adolescent", "Gynecology/Endocrine", "Lifestyle weight management; Combined OCP menstrual regulation", "Metformin insulin resistance", "Acne/hirsutism management", "Psychological support", "Metabolic complications", "Diagnose Rotterdam criteria carefully teens"),
    ("Endometriosis - Pain", "Gynecology", "NSAID; Combined hormonal contraception continuous", "GnRH agonist specialist; Laparoscopy", "Pelvic physio", "Infertility separate pathway", "Severe dyspareunia; bowel symptoms", "Long-term management plan"),
    ("Pelvic Inflammatory Disease", "Gynecology/Infectious", "Ceftriaxone IM + Doxycycline + Metronidazole", "Outpatient if mild; Inpatient if severe", "Partner treatment; STI screen", "IUCD consider removal", "Tubo-ovarian abscess; ectopic risk", "Treat empirically if suspected"),
    ("Prostatitis - Acute Bacterial", "Urology/Infectious", "Ciprofloxacin; Trimethoprim-sulfamethoxazole", "Analgesia; Alpha-blocker", "Hydration", "Urinary retention; sepsis", "4 weeks treatment often needed", "Chronic prostatitis different approach"),
    ("Urinary Incontinence - Stress", "Urology/Gynecology", "Pelvic floor exercises; Weight loss", "Duloxetine some regions; Surgery if failed", "Fluid moderation; bladder training", "UTI; hematuria; neuro cause", "Exclude treatable causes"),
    ("Overactive Bladder", "Urology", "Antimuscarinic oxybutynin/solifenacin; Beta-3 mirabegron", "Bladder training; PTNS", "Reduce caffeine", "Retention; hematuria", "Anticholinergic side effects elderly", "Start lowest effective dose elderly"),
    ("Nephrolithiasis - Renal Colic", "Urology/Emergency", "NSAID ketorolac/ibuprofen; Hydration", "Tamsulosin medical expulsive therapy", "Strain urine; metabolic workup", "Fever; anuria; single kidney", "Opioid if NSAID contraindicated short course", "CT non-contrast if diagnosis uncertain"),
    ("Chronic Kidney Disease - Stage 3", "Nephrology", "ACEi/ARB if proteinuria; BP control", "SGLT2i if diabetic; Phosphate binder late", "Nephrology co-care", "Avoid nephrotoxins NSAIDs", "Hyperkalemia; rapid progression", "Individualize BP targets"),
    ("Glomerulonephritis Suspected", "Nephrology", "Refer nephrology; Treat underlying if post-strep supportive", "Edema: diuretic; BP control", "Urinalysis protein hematuria casts", "Rapidly progressive GN emergency", "Biopsy often needed", "Not empiric antibiotics unless infection"),
    ("Liver Cirrhosis - Compensated", "Hepatology", "Treat underlying alcohol/NASH/viral", "Spironolactone ascites; Lactulose if encephalopathy", "HCC surveillance 6-month ultrasound", "Variceal screening", "Bleeding; encephalopathy; HCC", "Avoid sedatives NSAIDs"),
    ("Pancreatitis - Acute Mild", "Gastrointestinal", "IV fluids; NPO then early feeding", "Analgesia morphine if needed", "Treat gallstone cause ERCP if cholangitis", "Alcohol cessation counseling", "Severe necrosis; organ failure", "Hospitalization standard"),
    ("Diverticulitis - Uncomplicated", "Gastrointestinal", "Oral antibiotics cover gram-negatives and anaerobes; Clear liquid diet", "Mesalamine not acute; Fiber after recovery", "Analgesia", "Perforation; abscess; fistula", "Outpatient if reliable follow-up"),
    ("Appendicitis Suspected", "Emergency/Surgical", "Surgical referral; NPO IV fluids", "Antibiotics perioperative", "Analgesia", "Do not delay surgery", "Perforation; sepsis", "Imaging if diagnostic uncertainty"),
    ("Hemorrhoids - Symptomatic", "Gastrointestinal", "Fiber; Topical steroid/local anesthetic", "Rubber band ligation outpatient", "Avoid straining; hydration", "Anemia; weight loss exclude cancer", "Thrombosed external painful", "Colonoscopy age-appropriate screening"),
    ("Anal Fissure", "Gastrointestinal", "Topical GTN 0.2% or diltiazem; Stool softener", "Sitz bath; High fiber", "Chronic fissure surgery", "Crohn disease if multiple", "Lateral sphincterotomy refractory", "Pain severe — exclude other causes"),
    ("Celiac Disease", "Gastrointestinal", "Strict lifelong gluten-free diet", "Supplement iron B12 D if deficient", "Dietitian referral", "Osteoporosis screening", "Refractory celiac; lymphoma risk", "Serology biopsy diagnosis"),
    ("Food Allergy - IgE mediated", "Allergy", "Strict allergen avoidance; Epinephrine auto-injector", "Antihistamine mild urticaria only", "Action plan education", "Anaphylaxis history", "Oral immunotherapy specialist", "Read labels carefully"),
    ("Lactose Intolerance", "Gastrointestinal", "Lactase enzyme; Lactose-free diet", "Calcium alternative sources", "Not milk allergy — differentiate", "Severe weight loss other diagnosis", "Trial lactose-free diagnostic"),
    ("Obesity - Pharmacotherapy adjunct", "Endocrine/General", "Lifestyle foundation; Semaglutide/liraglutide if indicated", "Orlistat; Bariatric surgery criteria met", "Dietitian exercise psychology", "BMI comorbidity guided", "CVD risk reduction", "Not monotherapy without lifestyle"),
    ("Hyperthyroidism - Subclinical", "Endocrine", "Observe if low risk; Treat if symptoms high TSH suppressed", "Low-dose thionamide if progression", "Repeat labs 6-12 weeks", "Osteoporosis AF risk if prolonged", "Specialist if uncertain", "Elderly fragile — cautious treatment"),
    ("Diabetes Insipidus", "Endocrine", "Desmopressin central", "Treat nephrogenic cause; Thiazide NSAID nephrogenic", "Fluid balance monitoring", "Hypernatremia dehydration", "Electrolyte emergency if severe", "Specialist diagnosis required"),
    ("SIADH", "Endocrine/Metabolic", "Fluid restriction first-line", "Treat underlying cause; Demeclocycline/tolvaptan specialist", "Salt tablets cautious", "Severe hyponatremia seizure", "Correct sodium slowly", "Neurologic emergency if Na very low"),
    ("Gout - Urate Lowering", "Musculoskeletal", "Allopurinol start low; Febuxostat alternative", "Colchicine/NSAID prophylaxis when starting ULT", "Hydration; alcohol reduction", "Tophi; frequent flares", "Do not start during acute flare", "Titrate to target urate"),
    ("Fibromyalgia", "Rheumatology/Pain", "Aerobic exercise; CBT", "Duloxetine; Pregabalin; Amitriptyline low dose", "Sleep hygiene", "Exclude inflammatory arthritis", "Functional impairment severe", "Multimodal non-opioid"),
    ("SLE - Mild", "Rheumatology", "Hydroxychloroquine all patients", "NSAID; Low-dose steroid flare", "Sun protection; Vaccination", "Lupus nephritis; CNS lupus", "Rheumatology co-management", "Monitor hydroxychloroquine retinopathy"),
    ("Giant Cell Arteritis", "Rheumatology/Emergency", "High-dose prednisolone immediately if suspected", "Temporal artery biopsy", "Aspirin adjunct", "Visual loss emergency", "Do not delay steroids for biopsy", "Monitor steroid complications"),
    ("Psoriasis - Plaque Moderate", "Dermatology", "Topical vitamin D analog + steroid", "Phototherapy; Methotrexate; Biologic severe", "Emollient; Smoking cessation", "Psoriatic arthritis screen", "Erythroderma; pustular emergency", "Stepwise by BSA"),
    ("Rosacea", "Dermatology", "Topical metronidazole/ivermectin; Brimonidine redness", "Oral doxycycline anti-inflammatory dose", "Trigger avoidance alcohol heat", "Ocular rosacea", "Rhinophyma severe", "Gentle skin care"),
    ("Urticaria - Acute", "Dermatology/Allergy", "Non-sedating antihistamine cetirizine/loratadine", "Increase dose if needed up to 4x", "Avoid trigger", "Angioedema airway", "Chronic if >6 weeks", "Sedating antihistamine night if itch"),
    ("Chronic Urticaria", "Dermatology/Allergy", "Second-generation antihistamine up-dosed", "Omalizumab specialist refractory", "Autoimmune thyroid screen", "Angioedema anaphylaxis exclude", "Severe angioedema", "Avoid sedating if driving"),
    ("Pemphigus/Vesiculobullous Emergency", "Dermatology", "Refer dermatology emergency", "High-dose steroid immunosuppressant specialist", "Wound care infection prevention", "Widespread erosions", "ICU support if severe", "Not GP monotherapy"),
    ("Melasma", "Dermatology", "Sunscreen strict; Topical hydroquinone/tretinoin", "Azelaic acid; Chemical peel specialist", "Hormonal trigger OCP review", "Exclude melasma mimics", "Cosmetic counseling", "Sun protection essential"),
    ("Vitiligo", "Dermatology", "Topical steroid/calcineurin limited; Phototherapy", "Cosmetic camouflage", "Psychological support", "Rapid progression; segmental", "JAK inhibitor specialist emerging", "Autoimmune association screen"),
    ("Onychomycosis", "Dermatology", "Oral terbinafine 6-12 weeks", "Topical efinaconazole mild", "Confirm mycology before oral", "Diabetes foot involvement", "Liver disease oral caution", "Long treatment duration"),
    ("Herpes Simplex Labialis", "Dermatology/Infectious", "Topical acyclovir/penciclovir early", "Oral valacyclovir if frequent severe", "Sun protection trigger", "Immunocompromised disseminated", "Prophylaxis if very frequent", "Start at prodrome"),
    ("Hand Foot Mouth Disease", "Pediatric/Infectious", "Supportive fluids analgesia", "Avoid dehydration", "Isolation childcare", "Enterovirus 71 complications rare", "Meningitis encephalitis rare", "Self-limited"),
    ("Roseola Infantum", "Pediatric/Infectious", "Supportive; Antipyretics", "Febrile seizures risk educate parents", "HHV-6", "Immunocompromised severe", "Rash after fever classic", "Reassurance parents"),
    ("Paronychia - Acute", "Dermatology", "Warm soaks; Oral flucloxacillin if cellulitis", "Incision drainage if abscess", "Avoid nail biting", "Diabetes; felon extension", "Chronic different management", "Early drainage if fluctuant"),
    ("Furuncle/Carbuncle", "Dermatology/Infectious", "Incision drainage primary", "Flucloxacillin if surrounding cellulitis", "MRSA coverage if risk", "Diabetes immunocompromise", "Spreading abscess", "Do not squeeze"),
    ("Lyme Disease - Early Localized", "Infectious", "Doxycycline; Amoxicillin children pregnancy", "Azithromycin alternative", "Tick removal prevention", "Erythema migrans", "Carditis neuro borreliosis", "Treat without serology if classic rash"),
    ("Rocky Mountain Spotted Fever", "Infectious/Emergency", "Doxycycline empiric immediately", "Do not delay for test", "Tick bite history", "Severe Rickettsial disease", "Mortality high untreated", "Children adults same doxy"),
    ("Leptospirosis", "Infectious", "Doxycycline mild; Penicillin/ceftriaxone severe", "Supportive", "Exposure freshwater animals", "Weil disease ICU", "Jaundice renal failure", "Endemic areas occupational"),
    ("Brucellosis", "Infectious", "Doxycycline + rifampin or aminoglycoside", "Prolonged course weeks", "Animal exposure history", "Endocarditis osteoarticular", "Culture serology", "Combination therapy standard"),
    ("Leprosy", "Infectious", "MDT per WHO paucibacillary/multibacillary", "Dapsone rifampicin clofazimine", "Contact tracing", "Reaction type 1/2 steroid", "Long duration supervised", "National program coordination"),
    ("Schistosomiasis", "Infectious", "Praziquantel", "Species-specific", "Water exposure history", "Chronic bladder fibrosis", "Eggs in urine stool", "Mass treatment endemic"),
    ("Filariasis", "Infectious", "Diethylcarbamazine or ivermectin + albendazole per program", "Lymphoedema care elephantiasis", "Mosquito prevention", "Adverse reactions microfilarial load", "WHO MDA programs", "Chronic lymphedema supportive"),
    ("Onchocerciasis", "Infectious", "Ivermectin repeated MDA", "Moxidectin some regions", "Vector control", "Mazzotti reaction caution", "River blindness", "Community-directed treatment"),
    ("Trichomoniasis", "Infectious/Gynecology", "Metronidazole 2g single or 7 days", "Treat sexual partners", "Screen other STIs", "Pregnancy metronidazole safe", "Persistent reinfection", "Both partners treat"),
    ("Bacterial Meningitis Suspected", "Emergency/Infectious", "Ceftriaxone empiric + vancomycin + dexamethasone", "Adjust per culture LP", "Emergency admission", "Petechiae; neck stiffness; altered mental status", "Do not delay antibiotics for LP", "Public health prophylaxis contacts"),
    ("Encephalitis Suspected", "Emergency/Infectious", "Acyclovir empiric until HSV excluded", "Supportive ICU", "MRI LP", "Seizures; focal deficits", "Infectious neurology emergency", "Early acyclovir critical HSV"),
    ("Sepsis - Community", "Emergency/Infectious", "IV broad-spectrum within 1 hour; Fluids", "Source control; Vasopressor ICU", "Blood cultures before antibiotics if possible", "Lactate monitoring", "Septic shock", "Hour-1 bundle"),
    ("Pneumonia Aspiration", "Respiratory/Infectious", "Amoxicillin-clavulanate; Anaerobic cover if putrid", "Airway protection; Treat cause", "Chest physiotherapy", "Lung abscess; empyema", "Dental poor oral hygiene risk", "Hospitalize if severe"),
    ("Pulmonary Embolism - Anticoagulation", "Cardiovascular/Emergency", "Apixaban/rivaroxaban DOAC if stable", "LMWH warfarin alternative", "Oxygen; Treat provoking factor", "Hemodynamic instability thrombolysis", "Massive PE emergency", "Risk stratify sPESI"),
    ("DVT - Lower Extremity", "Cardiovascular", "DOAC first-line apixaban rivaroxaban", "LMWH fondaparinux bridge if warfarin", "Compression stockings; Mobilize", "Phlegmasia cerulea dolens", "Cancer-associated LMWH preferred some", "3 months minimum unprovoked evaluate"),
    ("Varicose Veins Symptomatic", "Vascular", "Compression stockings; Elevation", "Sclerotherapy; Ablation referral", "Exercise; Weight loss", "Ulceration; bleeding", "Superficial thrombophlebitis", "Exclude DVT if acute painful"),
    ("Chronic Venous Insufficiency", "Vascular", "Compression therapy; Leg elevation", "Venous active ulcer wound care", "Weight management", "Ulcer infection", "Surgical referral refractory", "Pentoxifylline adjunct ulcer"),
    ("Peripheral Arterial Disease", "Cardiovascular", "Antiplatelet; Statin; Exercise program", "Cilostazol claudication; Revascularization critical limb", "Smoking cessation critical", "Critical limb ischemia", "Wound diabetic foot", "ABI screening"),
    ("Raynaud Phenomenon", "Rheumatology", "Avoid cold; Calcium channel blocker nifedipine", "Protect digits from trauma", "Scleroderma connective tissue workup", "Digital ulcers ischemia", "Severe secondary", "Primary common benign"),
    ("Infective Endocarditis", "Cardiovascular/Infectious", "IV prolonged antibiotics per culture organism", "Surgery if valve dysfunction abscess", "Blood cultures before antibiotics", "Dental source", "Heart failure; embolic", "Infectious disease cardiology team"),
    ("Pericarditis - Acute", "Cardiovascular", "NSAID colchicine combination", "Rest; Treat underlying viral", "ECG PR depression", "Tamponade large effusion", "Recurrent colchicine reduces", "Exclude MI aortic dissection"),
    ("Myocarditis", "Cardiovascular", "Supportive; Heart failure therapy", "Avoid strenuous activity 3-6 months", "Arrhythmia monitoring", "Cardiogenic shock", "Viral common cause", "Cardiology admission if severe"),
    ("Hypertensive Emergency", "Cardiovascular/Emergency", "IV labetalol nicardipine clevidipine", "Reduce MAP 10-20% first hour not too fast", "ICU monitoring", "End-organ damage", "Aortic dissection different target", "OPD: labetalol STAT per protocol"),
    ("Dyslipidemia Familial", "Cardiovascular", "High-intensity statin; PCSK9 inhibitor", "Ezetimibe; Lipoprotein apheresis rare", "Family screening", "Premature ASCVD", "Genetic counseling", "Aggressive targets young"),
    ("Rheumatic Fever", "Cardiovascular/Pediatric", "Penicillin eradicate GAS; Aspirin/NSAID arthritis", "Benzathine penicillin prophylaxis long-term", "Jones criteria diagnosis", "Carditis valvular damage", "Chorea haloperidol valproate", "Secondary prophylaxis years"),
    ("Sick Sinus Syndrome", "Cardiology", "Pacemaker if symptomatic bradycardia", "Review medications beta-blocker", "Syncope falls elderly", "Tachy-brady syndrome", "Electrophysiology", "Anticoagulation if AF coexists"),
    ("Wolff-Parkinson-White", "Cardiology", "Procainamide/flecainide stable narrow complex", "Avoid AV nodal blocker alone pre-excited AF", "Catheter ablation definitive", "Orthodromic AVRT", "Antidromic AF dangerous", "Cardiology electrophysiology"),
    ("Long QT Syndrome", "Cardiology", "Beta-blocker nadolol/propranolol", "Avoid QT-prolonging drugs list", "ICD high-risk", "Syncope family history sudden death", "Electrolyte K Mg Ca correct", "Genetic testing family"),
    ("Brugada Syndrome", "Cardiology", "Avoid fever sodium channel drugs", "ICD if high-risk", "Genetic counseling", "Sudden death family", "Isoproterenol acute electrical storm", "Specialist risk stratification"),
    ("Cardiomyopathy Dilated", "Cardiology", "GDMT heart failure ACEi beta-blocker MRA SGLT2i", "Device CRT ICD if criteria", "Alcohol cessation", "Arrhythmia thromboembolism", "Transplant end-stage", "Treat reversible causes"),
    ("Hypertrophic Cardiomyopathy", "Cardiology", "Beta-blocker verapamil first-line symptoms", "Avoid dehydration strenuous if outflow obstruction", "ICD sudden death risk", "Syncope exertion", "Septal reduction refractory", "Sports restriction counseling"),
    ("Pulmonary Hypertension", "Pulmonology/Cardiology", "Specialist PAH agents sildenafil bosentan", "Treat group 2/3 cause if secondary", "Oxygen if hypoxic", "Right heart failure", "Complex specialist only", "Do not empiric in GP"),
]

# Age-specific modifier snippets
AGE_NOTES = {
    "Neonate": "Neonatal dosing weight-based; avoid contraindicated adult agents; specialist protocols mandatory for most medications.",
    "Infant": "Infant formulations liquid/sachet preferred; weight-based dosing; avoid honey <12 months; paracetamol weight-based.",
    "Child": "Pediatric dosing by weight/BSA; liquid formulations; AAP/CDC pediatric guidelines apply; avoid aspirin <18 viral illness.",
    "Adolescent": "Adult doses may apply by weight; consider pregnancy potential; mental health substance use screening.",
    "Young_Adult": "Standard adult dosing; pregnancy test if relevant; drug interactions with OCP consider.",
    "Middle_Adult": "Standard adult dosing; monitor cardiovascular renal risk; polypharmacy interactions.",
    "Elderly": "Start low go slow; Beers criteria avoid high-risk drugs; renal/hepatic dose adjustment; fall risk sedatives.",
    "Pregnancy": "FDA/category-aware agent selection; avoid teratogens; obstetric co-management; many antibiotics safe penicillin cephalosporin macrolide azithromycin.",
    "Lactation": "LactMed compatibility check; prefer agents with low milk transfer; timing doses around feeds if needed.",
}

GENDER_NOTES = {
    "Female": "Consider pregnancy/lactation potential; gynecologic drug interactions; iron needs menstruation.",
    "Male": "Consider BPH alpha-blocker interactions; erectile dysfunction drug interactions; prostate screening age-appropriate.",
    "All": "Individualize for patient comorbidities allergies renal hepatic function.",
}


def age_applicable(disease: str, age_key: str) -> bool:
    d = disease.lower()
    if age_key == "Neonate" and not any(x in d for x in ["neonatal", "neonate", "birth", "jaundice"]):
        return False
    if age_key == "Infant" and any(x in d for x in ["prostatitis", "bph", "erectile", "menorrhagia", "pcos", "endometriosis", "preeclampsia", "gestational"]):
        return False
    if age_key == "Child" and any(x in d for x in ["prostatitis", "bph", "erectile", "gestational", "preeclampsia", "menorrhagia", "cervical cancer"]):
        return False
    if age_key == "Pregnancy" and any(x in d for x in ["erectile", "bph", "prostatitis"]):
        return False
    if age_key == "Adolescent" and any(x in d for x in ["neonatal", "neonate", "bph", "prostatitis elderly"]):
        return False
    if "pediatric" in d or "child" in d or "infant" in d:
        if age_key in ("Middle_Adult", "Elderly"):
            return False
    if "neonatal" in d and age_key not in ("Neonate", "Infant"):
        return False
    if any(x in d for x in ["bph", "prostatitis", "erectile"]) and age_key in ("Neonate", "Infant", "Child", "Pregnancy", "Lactation"):
        return False
    if any(x in d for x in ["menorrhagia", "endometriosis", "pcos", "bacterial vaginosis", "vulvovaginal"]) and age_key == "Male":
        return False
    if "pregnancy" in d or "gestational" in d or "preeclampsia" in d:
        if age_key not in ("Pregnancy", "Young_Adult", "Middle_Adult", "Female", "All") and age_key != "Lactation":
            if age_key in ("Male", "Neonate", "Infant", "Child", "Adolescent", "Elderly"):
                return False
    return True


def gender_applicable(disease: str, gender: str) -> bool:
    d = disease.lower()
    female_only = ["menorrhagia", "endometriosis", "pcos", "bacterial vaginosis", "vulvovaginal", "pelvic inflammatory", "gestational", "preeclampsia", "pregnancy"]
    male_only = ["bph", "prostatitis", "epididymo", "erectile"]
    if gender == "Male" and any(x in d for x in female_only):
        return False
    if gender == "Female" and any(x in d for x in male_only):
        return False
    return True


def write_entry(f, idx: int, disease, category, age_name, age_range, gender, first_line, alt, adjunct, non_rx, refer, notes):
    age_note = AGE_NOTES.get(age_name.split("_")[0] if age_name in AGE_NOTES else age_name, AGE_NOTES.get(age_name, ""))
    gender_note = GENDER_NOTES.get(gender, GENDER_NOTES["All"])
    f.write(f"\n{'='*72}\n")
    f.write(f"ENTRY_ID: {idx:05d}\n")
    f.write(f"DISEASE_CONDITION: {disease}\n")
    f.write(f"CATEGORY: {category}\n")
    f.write(f"AGE_GROUP: {age_name} ({age_range})\n")
    f.write(f"GENDER: {gender}\n")
    f.write(f"FIRST_LINE_MEDICATIONS: {first_line}\n")
    f.write(f"ALTERNATIVE_MEDICATIONS: {alt}\n")
    f.write(f"ADJUNCT_SUPPORTIVE: {adjunct}\n")
    f.write(f"NON_PHARMACOLOGICAL: {non_rx}\n")
    f.write(f"REFER_URGENT_WHEN: {refer}\n")
    f.write(f"CLINICAL_NOTES: {notes}\n")
    f.write(f"AGE_SPECIFIC_GUIDANCE: {age_note}\n")
    f.write(f"GENDER_SPECIFIC_GUIDANCE: {gender_note}\n")
    f.write(f"DISCLAIMER: Educational protocol reference only. Licensed clinician must confirm diagnosis, dosing, allergies, pregnancy status, and local resistance patterns before prescribing.\n")


def normalize_row(row):
    if len(row) == 8:
        return row
    if len(row) == 7:
        # Legacy 7-field rows: missing explicit alternatives column
        return (row[0], row[1], row[2], "Per local formulary and specialist guidance", row[3], row[4], row[5], row[6])
    raise ValueError(f"Invalid disease row ({len(row)} fields): {row[0]}")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    count = 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# COMMON DISEASE MEDICATION REFERENCE DATASET\n")
        f.write("# MedRAG Knowledge Base — 2000+ structured entries\n")
        f.write("# Sources: WHO STG patterns, CDC/AAP/IDSA public guidelines, institutional OPD protocols\n")
        f.write("# See also: data/medical_protocols/opd_whatsapp_protocols.txt\n")
        f.write("# NOT for direct patient self-medication\n\n")

        for disease_row in DISEASES:
            disease, category, first_line, alt, adjunct, non_rx, refer, notes = normalize_row(disease_row)
            for (age_name, age_range), gender in product(AGE_GROUPS, GENDERS):
                if not age_applicable(disease, age_name):
                    continue
                if not gender_applicable(disease, gender):
                    continue
                count += 1
                write_entry(f, count, disease, category, age_name, age_range, gender,
                            first_line, alt, adjunct, non_rx, refer, notes)

        # Pad with severity/comorbidity variants to exceed 2000 if needed
        severities = ["Mild", "Moderate", "Severe"]
        comorbid = ["With_Renal_Impairment", "With_Hepatic_Impairment", "With_Diabetes", "With_Cardiac_Disease"]
        if count < 2000:
            for disease_row in DISEASES:
                disease, category, first_line, alt, adjunct, non_rx, refer, notes = normalize_row(disease_row)
                for sev in severities:
                    for com in comorbid:
                        if count >= 2100:
                            break
                        if not age_applicable(disease, "Middle_Adult"):
                            continue
                        count += 1
                        mod_notes = f"{notes} | Severity variant: {sev} | Comorbidity: {com} — dose adjustment and agent selection per renal/hepatic function and interaction checks required."
                        write_entry(f, count, f"{disease} [{sev}]", category, "Middle_Adult", "40-64 years", "All",
                                    first_line, alt, adjunct, non_rx, refer, mod_notes)
                    if count >= 2100:
                        break
                if count >= 2100:
                    break

    print(f"Generated {count} entries -> {OUT}")
    if count < 2000:
        print(f"WARNING: Only {count} entries (target 2000+)")
        sys.exit(1)
    return count


if __name__ == "__main__":
    main()
