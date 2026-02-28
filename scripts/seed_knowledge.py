# VaaniSeva - Seed Script
# Run this ONCE to populate DynamoDB with government scheme data
# python scripts/seed_knowledge.py

import boto3
import json
import os
import math
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
bedrock  = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])

knowledge_table = dynamodb.Table(os.environ["DYNAMODB_KNOWLEDGE_TABLE"])
vectors_table   = dynamodb.Table(os.environ["DYNAMODB_VECTORS_TABLE"])

# ── Scheme data ───────────────────────────────────────────────
SCHEMES = [
    {
        "scheme_id": "pm-kisan",
        "section_id": "overview",
        "name_en": "PM-Kisan",
        "name_hi": "पीएम किसान",
        "text_en": "PM-Kisan gives Rs 6000 per year directly to farmer families. The money comes in 3 payments of Rs 2000 each. Any farmer who owns farmland can apply.",
        "text_hi": "पीएम किसान योजना में किसान परिवारों को हर साल 6000 रुपये मिलते हैं। यह पैसा 2000-2000 रुपये की तीन किस्तों में आता है। जिस किसान के पास खेती की जमीन है, वो आवेदन कर सकता है।",
        "eligibility_en": "Farmer families who own cultivable land. Not available for income tax payers, government employees, or professionals.",
        "eligibility_hi": "जिन किसान परिवारों के पास खेती योग्य जमीन हो। आयकर देने वाले, सरकारी कर्मचारी और पेशेवरों को नहीं मिलेगी।",
        "how_to_apply_en": "Visit nearest CSC center or pmkisan.gov.in with Aadhaar card, bank passbook, and land documents.",
        "helpline": "155261",
        "website": "pmkisan.gov.in"
    },
    {
        "scheme_id": "ayushman-bharat",
        "section_id": "overview",
        "name_en": "Ayushman Bharat",
        "name_hi": "आयुष्मान भारत",
        "text_en": "Ayushman Bharat gives free health insurance of Rs 5 lakh per year to poor families. You can get free treatment at government and empanelled private hospitals.",
        "text_hi": "आयुष्मान भारत योजना गरीब परिवारों को हर साल 5 लाख रुपये तक का मुफ्त स्वास्थ्य बीमा देती है। सरकारी और सूचीबद्ध निजी अस्पतालों में मुफ्त इलाज मिलता है।",
        "eligibility_en": "Families listed in SECC 2011 data. Includes daily wage workers, construction workers, domestic workers. Check eligibility at mera.pmjay.gov.in",
        "eligibility_hi": "SECC 2011 सूची में शामिल परिवार। दैनिक मजदूर, निर्माण कार्यकर्ता, घरेलू कामगार शामिल हैं। mera.pmjay.gov.in पर जांचें।",
        "how_to_apply_en": "Visit nearest Ayushman Bharat empanelled hospital or CSC with Aadhaar. No registration needed if already listed.",
        "helpline": "14555",
        "website": "pmjay.gov.in"
    },
    {
        "scheme_id": "mgnrega",
        "section_id": "overview",
        "name_en": "MGNREGA",
        "name_hi": "मनरेगा",
        "text_en": "MGNREGA guarantees 100 days of paid work per year to rural families. The daily wage is around Rs 200-300 depending on your state. Any adult in a rural household can apply.",
        "text_hi": "मनरेगा ग्रामीण परिवारों को साल में 100 दिन काम की गारंटी देती है। राज्य के अनुसार रोज 200-300 रुपये मजदूरी मिलती है। ग्रामीण घर का कोई भी वयस्क आवेदन कर सकता है।",
        "eligibility_en": "Any adult member of a rural household willing to do unskilled manual work. Apply at the local gram panchayat office.",
        "eligibility_hi": "ग्रामीण घर का कोई भी वयस्क सदस्य जो अकुशल शारीरिक काम करने को तैयार हो। स्थानीय ग्राम पंचायत में आवेदन करें।",
        "how_to_apply_en": "Go to your gram panchayat office with Aadhaar and bank account details. You will get a job card within 15 days.",
        "helpline": "1800-111-555",
        "website": "nrega.nic.in"
    },
    {
        "scheme_id": "pm-awas-yojana",
        "section_id": "overview",
        "name_en": "PM Awas Yojana",
        "name_hi": "पीएम आवास योजना",
        "text_en": "PM Awas Yojana gives money to build or improve homes for poor families. Rural families can get up to Rs 1.2 lakh and urban families can get home loan subsidy.",
        "text_hi": "पीएम आवास योजना गरीब परिवारों को घर बनाने या सुधारने के लिए पैसे देती है। ग्रामीण परिवारों को 1.2 लाख रुपये तक मिल सकते हैं और शहरी परिवारों को होम लोन सब्सिडी मिलती है।",
        "eligibility_en": "Families without pucca house, EWS/LIG income groups. Not for families who already own a pucca house anywhere in India.",
        "eligibility_hi": "जिन परिवारों के पास पक्का मकान नहीं है, EWS/LIG आय वर्ग। जिनके पास पहले से पक्का मकान हो, उन्हें नहीं मिलेगा।",
        "how_to_apply_en": "Apply at gram panchayat (rural) or urban local body office with Aadhaar, income certificate, and bank details.",
        "helpline": "1800-11-6163",
        "website": "pmaymis.gov.in"
    },
    {
        "scheme_id": "sukanya-samriddhi",
        "section_id": "overview",
        "name_en": "Sukanya Samriddhi Yojana",
        "name_hi": "सुकन्या समृद्धि योजना",
        "text_en": "Sukanya Samriddhi is a savings scheme for girl children. You deposit money and get high interest. The money can be used for her education or marriage after she turns 18.",
        "text_hi": "सुकन्या समृद्धि बेटियों के लिए बचत योजना है। पैसे जमा करने पर अच्छा ब्याज मिलता है। 18 साल बाद यह पैसा उसकी पढ़ाई या शादी में काम आता है।",
        "eligibility_en": "Any girl child below 10 years of age. Account opened by parent or guardian at post office or bank.",
        "eligibility_hi": "10 साल से कम उम्र की कोई भी बेटी। माता-पिता या अभिभावक पोस्ट ऑफिस या बैंक में खाता खोल सकते हैं।",
        "how_to_apply_en": "Visit nearest post office or bank with girl's birth certificate, parent Aadhaar, and address proof. Minimum deposit Rs 250.",
        "helpline": "1800-266-6868",
        "website": "nari.nic.in"
    },
    # ── 10 additional schemes (source: respective official GOI portals) ──────
    {
        # Source: mudra.org.in
        "scheme_id": "pm-mudra-yojana",
        "section_id": "overview",
        "name_en": "Pradhan Mantri Mudra Yojana",
        "name_hi": "प्रधान मंत्री मुद्रा योजना",
        "text_en": "PM Mudra gives business loans up to Rs 20 lakh to small traders, shopkeepers, artisans, and micro entrepreneurs. Loans come in four types: Shishu (up to Rs 50,000), Kishore (up to Rs 5 lakh), Tarun (up to Rs 10 lakh), and TarunPlus (up to Rs 20 lakh).",
        "text_hi": "पीएम मुद्रा योजना छोटे व्यापारियों, दुकानदारों, कारीगरों और सूक्ष्म उद्यमियों को 20 लाख रुपये तक का व्यवसाय ऋण देती है। शिशु (50,000 तक), किशोर (5 लाख तक), तरुण (10 लाख तक) और तरुण प्लस (20 लाख तक) नाम के चार प्रकार हैं।",
        "eligibility_en": "Any non-farm, non-corporate small or micro business owner. Includes vegetable vendors, tailors, repair shops, beauty parlours, small manufacturers.",
        "eligibility_hi": "कृषि से इतर कोई भी छोटा या सूक्ष्म व्यवसाय – सब्जी विक्रेता, दर्जी, मरम्मत की दुकान, ब्यूटी पार्लर, छोटे निर्माता।",
        "how_to_apply_en": "Apply at any bank, NBFC, or MFI branch, or online at udyamimitra.in. Carry Aadhaar, business proof, and bank account details.",
        "helpline": "1800-180-1111",
        "website": "mudra.org.in"
    },
    {
        # Source: pmfby.gov.in
        "scheme_id": "pm-fasal-bima",
        "section_id": "overview",
        "name_en": "Pradhan Mantri Fasal Bima Yojana",
        "name_hi": "प्रधान मंत्री फसल बीमा योजना",
        "text_en": "PM Fasal Bima gives crop insurance to farmers. Farmers pay only 2% premium for Kharif crops, 1.5% for Rabi crops, and 5% for commercial crops. The government pays the remaining premium, and full compensation is paid for crop loss.",
        "text_hi": "पीएम फसल बीमा किसानों को फसल बर्बाद होने पर मुआवजा देती है। खरीफ फसल पर केवल 2%, रबी पर 1.5% और व्यावसायिक फसल पर 5% प्रीमियम देना होता है। बाकी प्रीमियम सरकार भरती है।",
        "eligibility_en": "All farmers including sharecroppers and tenant farmers growing notified crops in notified areas. Loanee farmers are enrolled automatically.",
        "eligibility_hi": "अधिसूचित क्षेत्रों में अधिसूचित फसल उगाने वाले सभी किसान, जिनमें बटाईदार और किरायेदार किसान भी शामिल हैं। कर्ज लेने वाले किसान स्वचालित रूप से नामांकित होते हैं।",
        "how_to_apply_en": "Apply before the cut-off date at nearest bank, CSC, or online at pmfby.gov.in. Carry land documents, Aadhaar, and bank passbook.",
        "helpline": "14447",
        "website": "pmfby.gov.in"
    },
    {
        # Source: npscra.nsdl.co.in / jansamarth.in
        "scheme_id": "atal-pension-yojana",
        "section_id": "overview",
        "name_en": "Atal Pension Yojana",
        "name_hi": "अटल पेंशन योजना",
        "text_en": "Atal Pension Yojana gives a guaranteed monthly pension of Rs 1000 to Rs 5000 after age 60 to workers in the unorganised sector. You choose your pension amount and pay a small monthly contribution based on your age.",
        "text_hi": "अटल पेंशन योजना असंगठित क्षेत्र के कामगारों को 60 साल के बाद 1000 से 5000 रुपये तक की गारंटीशुदा मासिक पेंशन देती है। आप पेंशन राशि चुनते हैं और उम्र के हिसाब से छोटा मासिक योगदान देते हैं।",
        "eligibility_en": "Indian citizens aged 18–40 years with a savings bank account and mobile number. Not for income tax payers (from October 2022).",
        "eligibility_hi": "18 से 40 वर्ष के भारतीय नागरिक जिनके पास बचत खाता और मोबाइल नंबर हो। अक्टूबर 2022 के बाद आयकर देने वाले पात्र नहीं हैं।",
        "how_to_apply_en": "Visit your bank or post office with Aadhaar and mobile number to open an APY account. Can also apply via net banking or mobile banking.",
        "helpline": "1800-110-069",
        "website": "npscra.nsdl.co.in"
    },
    {
        # Source: pmsvanidhi.mohua.gov.in
        "scheme_id": "pm-svanidhi",
        "section_id": "overview",
        "name_en": "PM SVANidhi",
        "name_hi": "पीएम स्वनिधि",
        "text_en": "PM SVANidhi gives working capital loans to street vendors. The first loan is Rs 10,000, the second is Rs 20,000, and the third is Rs 50,000. Vendors who repay on time get a higher loan next time and interest subsidy.",
        "text_hi": "पीएम स्वनिधि रेहड़ी-पटरी वालों को कार्यशील पूंजी ऋण देती है। पहला ऋण 10,000, दूसरा 20,000 और तीसरा 50,000 रुपये का होता है। समय पर चुकाने पर अगली बार बड़ा ऋण और ब्याज सब्सिडी मिलती है।",
        "eligibility_en": "Street vendors who were vending on or before March 24, 2020, and hold a Certificate of Vending or Letter of Recommendation from Urban Local Body.",
        "eligibility_hi": "24 मार्च 2020 को या उससे पहले फेरी लगाने वाले विक्रेता जिनके पास वेंडिंग सर्टिफिकेट या शहरी स्थानीय निकाय का अनुशंसा पत्र हो।",
        "how_to_apply_en": "Apply online at pmsvanidhi.mohua.gov.in or through PM SVANidhi mobile app. Check eligibility first, then apply for Letter of Recommendation and loan.",
        "helpline": "1800-11-1979",
        "website": "pmsvanidhi.mohua.gov.in"
    },
    {
        # Source: wcd.nic.in/bbbp-schemes
        "scheme_id": "beti-bachao-beti-padhao",
        "section_id": "overview",
        "name_en": "Beti Bachao Beti Padhao",
        "name_hi": "बेटी बचाओ बेटी पढ़ाओ",
        "text_en": "Beti Bachao Beti Padhao is a government campaign to save and educate girl children. It works to stop female foeticide, improve girls' enrollment in school, and support their education and health. It runs through three ministries: Women & Child Development, Health, and Education.",
        "text_hi": "बेटी बचाओ बेटी पढ़ाओ अभियान बेटियों को बचाने और पढ़ाने के लिए है। यह कन्या भ्रूण हत्या रोकने, स्कूल में लड़कियों का नामांकन बढ़ाने और उनके स्वास्थ्य व शिक्षा को सहयोग देने के लिए चलाया जाता है।",
        "eligibility_en": "All girl children in India. Focus districts with low Child Sex Ratio. Benefits available via health, education, and social welfare departments.",
        "eligibility_hi": "भारत की सभी बालिकाएं। कम बाल लिंगानुपात वाले जिलों पर विशेष ध्यान। स्वास्थ्य, शिक्षा और सामाजिक कल्याण विभाग के माध्यम से लाभ मिलता है।",
        "how_to_apply_en": "Contact your Anganwadi worker, ASHA, or district Women & Child Development office. Benefits flow through hospital registration and school enrollment.",
        "helpline": "181",
        "website": "wcd.nic.in"
    },
    {
        # Source: nhm.gov.in (JSY guidelines under NHM)
        "scheme_id": "janani-suraksha-yojana",
        "section_id": "overview",
        "name_en": "Janani Suraksha Yojana",
        "name_hi": "जननी सुरक्षा योजना",
        "text_en": "Janani Suraksha Yojana gives cash to pregnant women who deliver in a government hospital or accredited private facility. In low-performing states, rural mothers get Rs 1400 and urban mothers get Rs 1000. The scheme aims to reduce maternal and infant deaths.",
        "text_hi": "जननी सुरक्षा योजना गर्भवती महिलाओं को सरकारी या मान्यताप्राप्त अस्पताल में प्रसव कराने पर नकद सहायता देती है। कम प्रदर्शन वाले राज्यों में ग्रामीण माताओं को 1400 और शहरी माताओं को 1000 रुपये मिलते हैं।",
        "eligibility_en": "All pregnant women who deliver in government or accredited private hospitals. Priority for BPL families, SC/ST women, and women above 19 years of age.",
        "eligibility_hi": "सरकारी या मान्यताप्राप्त निजी अस्पताल में प्रसव कराने वाली सभी गर्भवती महिलाएं। बीपीएल, अनुसूचित जाति/जनजाति और 19 वर्ष से अधिक उम्र की महिलाओं को प्राथमिकता।",
        "how_to_apply_en": "Register at your nearest PHC/sub-centre or government hospital during antenatal checkup. ASHA worker will assist with paperwork and cash transfer.",
        "helpline": "1800-180-1104",
        "website": "nhm.gov.in"
    },
    {
        # Source: dfpd.gov.in (PMGKAY merged into NFSA from Jan 2023)
        "scheme_id": "pm-garib-kalyan-anna",
        "section_id": "overview",
        "name_en": "PM Garib Kalyan Anna Yojana",
        "name_hi": "प्रधान मंत्री गरीब कल्याण अन्न योजना",
        "text_en": "PM Garib Kalyan Anna Yojana gives 5 kg of free foodgrain every month to each member of Antyodaya and Priority Household families. The scheme has been extended and merged into the National Food Security Act, ensuring free grain until 2028.",
        "text_hi": "पीएम गरीब कल्याण अन्न योजना अंत्योदय और प्राथमिक घरेलू परिवार के प्रत्येक सदस्य को हर महीने 5 किलो मुफ्त अनाज देती है। यह योजना राष्ट्रीय खाद्य सुरक्षा अधिनियम में शामिल हो गई है और 2028 तक लागू है।",
        "eligibility_en": "Families with Antyodaya Anna Yojana (AAY) or Priority Household (PHH) ration cards under the National Food Security Act.",
        "eligibility_hi": "राष्ट्रीय खाद्य सुरक्षा अधिनियम के तहत अंत्योदय अन्न योजना (AAY) या प्राथमिक घरेलू (PHH) राशन कार्ड वाले परिवार।",
        "how_to_apply_en": "No separate application needed. Collect free grain every month from your Fair Price Shop (ration shop) using your ration card and Aadhaar.",
        "helpline": "1967",
        "website": "dfpd.gov.in"
    },
    {
        # Source: pmjdy.gov.in
        "scheme_id": "pmjdy-jan-dhan",
        "section_id": "overview",
        "name_en": "Pradhan Mantri Jan Dhan Yojana",
        "name_hi": "प्रधान मंत्री जन धन योजना",
        "text_en": "PM Jan Dhan gives a zero-balance bank account with a free RuPay debit card to every unbanked Indian. You also get Rs 2 lakh accident insurance, Rs 30,000 life insurance, and an Rs 10,000 overdraft facility after good account history.",
        "text_hi": "पीएम जन धन हर अनबैंक्ड भारतीय को मुफ्त RuPay डेबिट कार्ड के साथ शून्य बैलेंस बैंक खाता देती है। साथ में 2 लाख रुपये का दुर्घटना बीमा, 30,000 रुपये का जीवन बीमा और अच्छे खाते के बाद 10,000 रुपये की ओवरड्राफ्ट सुविधा मिलती है।",
        "eligibility_en": "Any Indian citizen aged 10 years and above who does not have a bank account. Documents: Aadhaar card or any officially valid document.",
        "eligibility_hi": "10 वर्ष से अधिक उम्र का कोई भी भारतीय नागरिक जिसका बैंक खाता न हो। आधार कार्ड या कोई भी सरकारी मान्य दस्तावेज चाहिए।",
        "how_to_apply_en": "Visit any bank branch or Business Correspondent (BC) outlet with Aadhaar. Account can be opened with zero balance. No minimum deposit required.",
        "helpline": "1800-11-0001",
        "website": "pmjdy.gov.in"
    },
    {
        # Source: pmuy.gov.in / petroleum.gov.in
        "scheme_id": "pm-ujjwala-yojana",
        "section_id": "overview",
        "name_en": "Pradhan Mantri Ujjwala Yojana",
        "name_hi": "प्रधान मंत्री उज्ज्वला योजना",
        "text_en": "PM Ujjwala gives a free LPG gas connection to women from poor households. The government provides Rs 1600 financial support for the connection, a free first gas cylinder, and a free stove. This protects women from harmful indoor cooking smoke.",
        "text_hi": "पीएम उज्ज्वला गरीब घरों की महिलाओं को मुफ्त एलपीजी गैस कनेक्शन देती है। सरकार 1600 रुपये की सहायता, पहला गैस सिलेंडर और चूल्हा मुफ्त देती है। इससे महिलाएं घर के अंदर के धुएं से बचती हैं।",
        "eligibility_en": "Adult women from BPL households, SC/ST families, PMAY beneficiaries, Antyodaya families, forest/river-island dwellers, and most backward class families.",
        "eligibility_hi": "बीपीएल घरों, अनुसूचित जाति/जनजाति, पीएमएवाई लाभार्थियों, अंत्योदय परिवारों, वन/द्वीप निवासियों और अत्यंत पिछड़े वर्गों की वयस्क महिलाएं।",
        "how_to_apply_en": "Apply online at pmuy.gov.in or visit your nearest LPG distributor with Aadhaar, BPL ration card, and bank account details.",
        "helpline": "1906",
        "website": "pmuy.gov.in"
    },
    {
        # Source: scholarships.gov.in
        "scheme_id": "national-scholarship-portal",
        "section_id": "overview",
        "name_en": "National Scholarship Portal",
        "name_hi": "राष्ट्रीय छात्रवृत्ति पोर्टल",
        "text_en": "The National Scholarship Portal is a single platform for all central and state government scholarships. Students from SC, ST, OBC, minority, and disabled communities can apply for pre-matric and post-matric scholarships for school and college studies.",
        "text_hi": "राष्ट्रीय छात्रवृत्ति पोर्टल केंद्र और राज्य सरकार की सभी छात्रवृत्तियों के लिए एक ही मंच है। एससी, एसटी, ओबीसी, अल्पसंख्यक और दिव्यांग समुदाय के छात्र स्कूल और कॉलेज की पढ़ाई के लिए प्री-मैट्रिक और पोस्ट-मैट्रिक छात्रवृत्ति के लिए आवेदन कर सकते हैं।",
        "eligibility_en": "Students from SC, ST, OBC, minority communities, and students with disabilities enrolled in schools or colleges. Income limits vary by scholarship.",
        "eligibility_hi": "एससी, एसटी, ओबीसी, अल्पसंख्यक समुदाय और दिव्यांग छात्र जो स्कूल या कॉलेज में पढ़ रहे हों। आय सीमा छात्रवृत्ति के अनुसार अलग-अलग है।",
        "how_to_apply_en": "Register on scholarships.gov.in with Aadhaar and generate a One-Time Registration (OTR) number. Apply before the deadline with academic and bank documents.",
        "helpline": "0120-6619540",
        "website": "scholarships.gov.in"
    },
]


def get_embedding(text: str) -> list:
    response = bedrock.invoke_model(
        modelId=os.environ["BEDROCK_EMBEDDING_MODEL_ID"],
        body=json.dumps({"inputText": text}),
        contentType="application/json",
        accept="application/json"
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def seed():
    print("Seeding knowledge base...")
    for scheme in SCHEMES:
        # Save to knowledge table
        knowledge_table.put_item(Item=scheme)
        print(f"  ✓ Knowledge: {scheme['scheme_id']}")

        # Generate embeddings for English and Hindi text, save to vectors table
        for lang in ["en", "hi"]:
            text_key = f"text_{lang}"
            text = scheme.get(text_key, "")
            if not text:
                continue

            print(f"    Generating embedding for {scheme['scheme_id']} ({lang})...")
            embedding = get_embedding(text)

            vectors_table.put_item(Item={
                "embedding_id": f"{scheme['scheme_id']}#{lang}",
                "scheme_id": scheme["scheme_id"],
                "section_id": scheme["section_id"],
                "language": lang,
                "text": text,
                f"text_{lang}": text,
                "embedding": embedding
            })
            print(f"    ✓ Vector stored: {scheme['scheme_id']} ({lang})")

    print("\nDone! Knowledge base seeded with 15 schemes.")


if __name__ == "__main__":
    seed()
