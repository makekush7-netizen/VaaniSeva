# VaaniSeva - Seed Script
# Run this ONCE to populate DynamoDB with government scheme data
# python scripts/seed_knowledge.py

import boto3
import json
import os
import math
from decimal import Decimal
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
        "category": "agriculture",
        "name_en": "PM-Kisan",
        "name_hi": "पीएम किसान",
        "text_en": "PM-Kisan gives Rs 6000 per year directly to farmer families. The money comes in 3 payments of Rs 2000 each. Any farmer who owns farmland can apply.",
        "text_hi": "पीएम किसान योजना में किसान परिवारों को हर साल 6000 रुपये मिलते हैं। यह पैसा 2000-2000 रुपये की तीन किस्तों में आता है। जिस किसान के पास खेती की जमीन है, वो आवेदन कर सकता है।",
        "eligibility_en": "Farmer families who own cultivable land. Not available for income tax payers, government employees, or professionals.",
        "eligibility_hi": "जिन किसान परिवारों के पास खेती योग्य जमीन हो। आयकर देने वाले, सरकारी कर्मचारी और पेशेवरों को नहीं मिलेगी।",
        "how_to_apply_en": "Visit nearest CSC center or pmkisan.gov.in with Aadhaar card, bank passbook, and land documents.",
        "how_to_apply_hi": "नजदीकी CSC केंद्र जाएं या pmkisan.gov.in पर जाकर आधार कार्ड, बैंक पासबुक और जमीन के कागजात लेकर आवेदन करें।",
        "documents_en": "Aadhaar card, bank account passbook (linked to Aadhaar), land ownership records (khatauni/khasra/land title), mobile number registered with Aadhaar.",
        "documents_hi": "आधार कार्ड, बैंक खाता पासबुक (आधार से लिंक), जमीन के कागजात (खतौनी/खसरा/भूमि स्वामित्व), आधार से जुड़ा मोबाइल नंबर।",
        "helpline": "155261",
        "website": "pmkisan.gov.in"
    },
    {
        "scheme_id": "ayushman-bharat",
        "section_id": "overview",
        "category": "health",
        "name_en": "Ayushman Bharat",
        "name_hi": "आयुष्मान भारत",
        "text_en": "Ayushman Bharat gives free health insurance of Rs 5 lakh per year to poor families. You can get free treatment at government and empanelled private hospitals.",
        "text_hi": "आयुष्मान भारत योजना गरीब परिवारों को हर साल 5 लाख रुपये तक का मुफ्त स्वास्थ्य बीमा देती है। सरकारी और सूचीबद्ध निजी अस्पतालों में मुफ्त इलाज मिलता है।",
        "eligibility_en": "Families listed in SECC 2011 data. Includes daily wage workers, construction workers, domestic workers. Check eligibility at mera.pmjay.gov.in",
        "eligibility_hi": "SECC 2011 सूची में शामिल परिवार। दैनिक मजदूर, निर्माण कार्यकर्ता, घरेलू कामगार शामिल हैं। mera.pmjay.gov.in पर जांचें।",
        "how_to_apply_en": "Visit nearest Ayushman Bharat empanelled hospital or CSC with Aadhaar. No registration needed if already listed.",
        "how_to_apply_hi": "नजदीकी आयुष्मान भारत सूचीबद्ध अस्पताल या CSC में आधार लेकर जाएं। अगर पहले से सूची में हैं तो अलग से पंजीकरण की जरूरत नहीं।",
        "documents_en": "Aadhaar card, ration card, SECC/RSBY card (if available), any government ID proof. Ayushman card is generated at the hospital or CSC.",
        "documents_hi": "आधार कार्ड, राशन कार्ड, SECC/RSBY कार्ड (अगर हो), कोई भी सरकारी पहचान पत्र। आयुष्मान कार्ड अस्पताल या CSC में बनता है।",
        "helpline": "14555",
        "website": "pmjay.gov.in"
    },
    {
        "scheme_id": "mgnrega",
        "section_id": "overview",
        "category": "finance",
        "name_en": "MGNREGA",
        "name_hi": "मनरेगा",
        "text_en": "MGNREGA guarantees 100 days of paid work per year to rural families. The daily wage is around Rs 200-300 depending on your state. Any adult in a rural household can apply.",
        "text_hi": "मनरेगा ग्रामीण परिवारों को साल में 100 दिन काम की गारंटी देती है। राज्य के अनुसार रोज 200-300 रुपये मजदूरी मिलती है। ग्रामीण घर का कोई भी वयस्क आवेदन कर सकता है।",
        "eligibility_en": "Any adult member of a rural household willing to do unskilled manual work. Apply at the local gram panchayat office.",
        "eligibility_hi": "ग्रामीण घर का कोई भी वयस्क सदस्य जो अकुशल शारीरिक काम करने को तैयार हो। स्थानीय ग्राम पंचायत में आवेदन करें।",
        "how_to_apply_en": "Go to your gram panchayat office with Aadhaar and bank account details. You will get a job card within 15 days.",
        "how_to_apply_hi": "ग्राम पंचायत कार्यालय में आधार और बैंक खाता जानकारी लेकर जाएं। 15 दिनों में जॉब कार्ड मिल जाएगा।",
        "documents_en": "Aadhaar card, passport-size photographs, bank account details, proof of residence in rural area. No income proof needed.",
        "documents_hi": "आधार कार्ड, पासपोर्ट साइज फोटो, बैंक खाता जानकारी, ग्रामीण क्षेत्र में निवास का प्रमाण। आय प्रमाण की जरूरत नहीं।",
        "helpline": "1800-111-555",
        "website": "nrega.nic.in"
    },
    {
        "scheme_id": "pm-awas-yojana",
        "section_id": "overview",
        "category": "housing",
        "name_en": "PM Awas Yojana",
        "name_hi": "पीएम आवास योजना",
        "text_en": "PM Awas Yojana gives money to build or improve homes for poor families. Rural families can get up to Rs 1.2 lakh and urban families can get home loan subsidy.",
        "text_hi": "पीएम आवास योजना गरीब परिवारों को घर बनाने या सुधारने के लिए पैसे देती है। ग्रामीण परिवारों को 1.2 लाख रुपये तक मिल सकते हैं और शहरी परिवारों को होम लोन सब्सिडी मिलती है।",
        "eligibility_en": "Families without pucca house, EWS/LIG income groups. Not for families who already own a pucca house anywhere in India.",
        "eligibility_hi": "जिन परिवारों के पास पक्का मकान नहीं है, EWS/LIG आय वर्ग। जिनके पास पहले से पक्का मकान हो, उन्हें नहीं मिलेगा।",
        "how_to_apply_en": "Apply at gram panchayat (rural) or urban local body office with Aadhaar, income certificate, and bank details.",
        "how_to_apply_hi": "ग्राम पंचायत (ग्रामीण) या शहरी स्थानीय निकाय कार्यालय में आधार, आय प्रमाण पत्र और बैंक जानकारी लेकर आवेदन करें।",
        "documents_en": "Aadhaar card, income certificate, bank account passbook, land documents (for rural), no-pucca-house certificate, caste certificate (if SC/ST), passport-size photographs.",
        "documents_hi": "आधार कार्ड, आय प्रमाण पत्र, बैंक खाता पासबुक, जमीन के कागजात (ग्रामीण के लिए), पक्का मकान न होने का प्रमाण पत्र, जाति प्रमाण पत्र (SC/ST के लिए), पासपोर्ट साइज फोटो।",
        "helpline": "1800-11-6163",
        "website": "pmaymis.gov.in"
    },
    {
        "scheme_id": "sukanya-samriddhi",
        "section_id": "overview",
        "category": "women",
        "name_en": "Sukanya Samriddhi Yojana",
        "name_hi": "सुकन्या समृद्धि योजना",
        "text_en": "Sukanya Samriddhi is a savings scheme for girl children. You deposit money and get high interest. The money can be used for her education or marriage after she turns 18.",
        "text_hi": "सुकन्या समृद्धि बेटियों के लिए बचत योजना है। पैसे जमा करने पर अच्छा ब्याज मिलता है। 18 साल बाद यह पैसा उसकी पढ़ाई या शादी में काम आता है।",
        "eligibility_en": "Any girl child below 10 years of age. Account opened by parent or guardian at post office or bank.",
        "eligibility_hi": "10 साल से कम उम्र की कोई भी बेटी। माता-पिता या अभिभावक पोस्ट ऑफिस या बैंक में खाता खोल सकते हैं।",
        "how_to_apply_en": "Visit nearest post office or bank with girl's birth certificate, parent Aadhaar, and address proof. Minimum deposit Rs 250.",
        "how_to_apply_hi": "नजदीकी पोस्ट ऑफिस या बैंक में बेटी का जन्म प्रमाण पत्र, माता-पिता का आधार और पते का प्रमाण लेकर जाएं। न्यूनतम जमा 250 रुपये।",
        "documents_en": "Girl child's birth certificate, parent/guardian Aadhaar card, parent/guardian address proof, passport-size photographs of parent and child, minimum deposit of Rs 250.",
        "documents_hi": "बेटी का जन्म प्रमाण पत्र, माता-पिता/अभिभावक का आधार कार्ड, पते का प्रमाण, माता-पिता और बच्ची की पासपोर्ट साइज फोटो, न्यूनतम 250 रुपये जमा।",
        "helpline": "1800-266-6868",
        "website": "nari.nic.in"
    },
    # ── 10 additional schemes (source: respective official GOI portals) ──────
    {
        # Source: mudra.org.in
        "scheme_id": "pm-mudra-yojana",
        "section_id": "overview",
        "category": "finance",
        "name_en": "Pradhan Mantri Mudra Yojana",
        "name_hi": "प्रधान मंत्री मुद्रा योजना",
        "text_en": "PM Mudra gives business loans up to Rs 20 lakh to small traders, shopkeepers, artisans, and micro entrepreneurs. Loans come in four types: Shishu (up to Rs 50,000), Kishore (up to Rs 5 lakh), Tarun (up to Rs 10 lakh), and TarunPlus (up to Rs 20 lakh).",
        "text_hi": "पीएम मुद्रा योजना छोटे व्यापारियों, दुकानदारों, कारीगरों और सूक्ष्म उद्यमियों को 20 लाख रुपये तक का व्यवसाय ऋण देती है। शिशु (50,000 तक), किशोर (5 लाख तक), तरुण (10 लाख तक) और तरुण प्लस (20 लाख तक) नाम के चार प्रकार हैं।",
        "eligibility_en": "Any non-farm, non-corporate small or micro business owner. Includes vegetable vendors, tailors, repair shops, beauty parlours, small manufacturers.",
        "eligibility_hi": "कृषि से इतर कोई भी छोटा या सूक्ष्म व्यवसाय – सब्जी विक्रेता, दर्जी, मरम्मत की दुकान, ब्यूटी पार्लर, छोटे निर्माता।",
        "how_to_apply_en": "Apply at any bank, NBFC, or MFI branch, or online at udyamimitra.in. Carry Aadhaar, business proof, and bank account details.",
        "how_to_apply_hi": "किसी भी बैंक, NBFC, या MFI शाखा में आवेदन करें या udyamimitra.in पर ऑनलाइन करें। आधार, व्यापार प्रमाण और बैंक खाता जानकारी लेकर जाएं।",
        "documents_en": "Aadhaar card, PAN card, business plan or project report, proof of business (shop registration, license, GST), bank account details, passport-size photographs, address proof.",
        "documents_hi": "आधार कार्ड, पैन कार्ड, व्यापार योजना या प्रोजेक्ट रिपोर्ट, व्यापार का प्रमाण (दुकान पंजीकरण, लाइसेंस, GST), बैंक खाता जानकारी, पासपोर्ट साइज फोटो, पते का प्रमाण।",
        "helpline": "1800-180-1111",
        "website": "mudra.org.in"
    },
    {
        # Source: pmfby.gov.in
        "scheme_id": "pm-fasal-bima",
        "section_id": "overview",
        "category": "agriculture",
        "name_en": "Pradhan Mantri Fasal Bima Yojana",
        "name_hi": "प्रधान मंत्री फसल बीमा योजना",
        "text_en": "PM Fasal Bima gives crop insurance to farmers. Farmers pay only 2% premium for Kharif crops, 1.5% for Rabi crops, and 5% for commercial crops. The government pays the remaining premium, and full compensation is paid for crop loss.",
        "text_hi": "पीएम फसल बीमा किसानों को फसल बर्बाद होने पर मुआवजा देती है। खरीफ फसल पर केवल 2%, रबी पर 1.5% और व्यावसायिक फसल पर 5% प्रीमियम देना होता है। बाकी प्रीमियम सरकार भरती है।",
        "eligibility_en": "All farmers including sharecroppers and tenant farmers growing notified crops in notified areas. Loanee farmers are enrolled automatically.",
        "eligibility_hi": "अधिसूचित क्षेत्रों में अधिसूचित फसल उगाने वाले सभी किसान, जिनमें बटाईदार और किरायेदार किसान भी शामिल हैं। कर्ज लेने वाले किसान स्वचालित रूप से नामांकित होते हैं।",
        "how_to_apply_en": "Apply before the cut-off date at nearest bank, CSC, or online at pmfby.gov.in. Carry land documents, Aadhaar, and bank passbook.",
        "how_to_apply_hi": "अंतिम तिथि से पहले नजदीकी बैंक, CSC या pmfby.gov.in पर ऑनलाइन आवेदन करें। जमीन के कागजात, आधार और बैंक पासबुक लेकर जाएं।",
        "documents_en": "Aadhaar card, bank account passbook, land ownership documents (khatauni/khasra), sowing certificate from Patwari, crop details and area sown.",
        "documents_hi": "आधार कार्ड, बैंक खाता पासबुक, जमीन के कागजात (खतौनी/खसरा), पटवारी से बुआई प्रमाण पत्र, फसल विवरण और बोया गया क्षेत्र।",
        "helpline": "14447",
        "website": "pmfby.gov.in"
    },
    {
        # Source: npscra.nsdl.co.in / jansamarth.in
        "scheme_id": "atal-pension-yojana",
        "section_id": "overview",
        "category": "finance",
        "name_en": "Atal Pension Yojana",
        "name_hi": "अटल पेंशन योजना",
        "text_en": "Atal Pension Yojana gives a guaranteed monthly pension of Rs 1000 to Rs 5000 after age 60 to workers in the unorganised sector. You choose your pension amount and pay a small monthly contribution based on your age.",
        "text_hi": "अटल पेंशन योजना असंगठित क्षेत्र के कामगारों को 60 साल के बाद 1000 से 5000 रुपये तक की गारंटीशुदा मासिक पेंशन देती है। आप पेंशन राशि चुनते हैं और उम्र के हिसाब से छोटा मासिक योगदान देते हैं।",
        "eligibility_en": "Indian citizens aged 18–40 years with a savings bank account and mobile number. Not for income tax payers (from October 2022).",
        "eligibility_hi": "18 से 40 वर्ष के भारतीय नागरिक जिनके पास बचत खाता और मोबाइल नंबर हो। अक्टूबर 2022 के बाद आयकर देने वाले पात्र नहीं हैं।",
        "how_to_apply_en": "Visit your bank or post office with Aadhaar and mobile number to open an APY account. Can also apply via net banking or mobile banking.",
        "how_to_apply_hi": "बैंक या पोस्ट ऑफिस में आधार और मोबाइल नंबर लेकर APY खाता खोलें। नेट बैंकिंग या मोबाइल बैंकिंग से भी आवेदन कर सकते हैं।",
        "documents_en": "Aadhaar card, savings bank account, mobile number linked to bank account. No other documents needed.",
        "documents_hi": "आधार कार्ड, बचत बैंक खाता, बैंक खाते से जुड़ा मोबाइल नंबर। कोई अन्य दस्तावेज की जरूरत नहीं।",
        "helpline": "1800-110-069",
        "website": "npscra.nsdl.co.in"
    },
    {
        # Source: pmsvanidhi.mohua.gov.in
        "scheme_id": "pm-svanidhi",
        "section_id": "overview",
        "category": "finance",
        "name_en": "PM SVANidhi",
        "name_hi": "पीएम स्वनिधि",
        "text_en": "PM SVANidhi gives working capital loans to street vendors. The first loan is Rs 10,000, the second is Rs 20,000, and the third is Rs 50,000. Vendors who repay on time get a higher loan next time and interest subsidy.",
        "text_hi": "पीएम स्वनिधि रेहड़ी-पटरी वालों को कार्यशील पूंजी ऋण देती है। पहला ऋण 10,000, दूसरा 20,000 और तीसरा 50,000 रुपये का होता है। समय पर चुकाने पर अगली बार बड़ा ऋण और ब्याज सब्सिडी मिलती है।",
        "eligibility_en": "Street vendors who were vending on or before March 24, 2020, and hold a Certificate of Vending or Letter of Recommendation from Urban Local Body.",
        "eligibility_hi": "24 मार्च 2020 को या उससे पहले फेरी लगाने वाले विक्रेता जिनके पास वेंडिंग सर्टिफिकेट या शहरी स्थानीय निकाय का अनुशंसा पत्र हो।",
        "how_to_apply_en": "Apply online at pmsvanidhi.mohua.gov.in or through PM SVANidhi mobile app. Check eligibility first, then apply for Letter of Recommendation and loan.",
        "how_to_apply_hi": "pmsvanidhi.mohua.gov.in पर ऑनलाइन या PM स्वनिधि मोबाइल ऐप से आवेदन करें। पहले पात्रता जांचें, फिर अनुशंसा पत्र और लोन के लिए आवेदन करें।",
        "documents_en": "Aadhaar card, Certificate of Vending (CoV) or Letter of Recommendation (LoR) from ULB, bank account details, passport-size photograph, mobile number.",
        "documents_hi": "आधार कार्ड, वेंडिंग सर्टिफिकेट (CoV) या शहरी निकाय से अनुशंसा पत्र (LoR), बैंक खाता जानकारी, पासपोर्ट साइज फोटो, मोबाइल नंबर।",
        "helpline": "1800-11-1979",
        "website": "pmsvanidhi.mohua.gov.in"
    },
    {
        # Source: wcd.nic.in/bbbp-schemes
        "scheme_id": "beti-bachao-beti-padhao",
        "section_id": "overview",
        "category": "women",
        "name_en": "Beti Bachao Beti Padhao",
        "name_hi": "बेटी बचाओ बेटी पढ़ाओ",
        "text_en": "Beti Bachao Beti Padhao is a government campaign to save and educate girl children. It works to stop female foeticide, improve girls' enrollment in school, and support their education and health. It runs through three ministries: Women & Child Development, Health, and Education.",
        "text_hi": "बेटी बचाओ बेटी पढ़ाओ अभियान बेटियों को बचाने और पढ़ाने के लिए है। यह कन्या भ्रूण हत्या रोकने, स्कूल में लड़कियों का नामांकन बढ़ाने और उनके स्वास्थ्य व शिक्षा को सहयोग देने के लिए चलाया जाता है।",
        "eligibility_en": "All girl children in India. Focus districts with low Child Sex Ratio. Benefits available via health, education, and social welfare departments.",
        "eligibility_hi": "भारत की सभी बालिकाएं। कम बाल लिंगानुपात वाले जिलों पर विशेष ध्यान। स्वास्थ्य, शिक्षा और सामाजिक कल्याण विभाग के माध्यम से लाभ मिलता है।",
        "how_to_apply_en": "Contact your Anganwadi worker, ASHA, or district Women & Child Development office. Benefits flow through hospital registration and school enrollment.",
        "how_to_apply_hi": "अपनी आंगनवाड़ी कार्यकर्ता, आशा कार्यकर्ता, या जिला महिला एवं बाल विकास कार्यालय से संपर्क करें। अस्पताल पंजीकरण और स्कूल नामांकन के माध्यम से लाभ मिलता है।",
        "documents_en": "Girl child's birth certificate, school enrollment proof, hospital registration records. No separate application form needed.",
        "documents_hi": "बालिका का जन्म प्रमाण पत्र, स्कूल नामांकन प्रमाण, अस्पताल पंजीकरण रिकॉर्ड। अलग आवेदन पत्र की जरूरत नहीं।",
        "helpline": "181",
        "website": "wcd.nic.in"
    },
    {
        # Source: nhm.gov.in (JSY guidelines under NHM)
        "scheme_id": "janani-suraksha-yojana",
        "section_id": "overview",
        "category": "health",
        "name_en": "Janani Suraksha Yojana",
        "name_hi": "जननी सुरक्षा योजना",
        "text_en": "Janani Suraksha Yojana gives cash to pregnant women who deliver in a government hospital or accredited private facility. In low-performing states, rural mothers get Rs 1400 and urban mothers get Rs 1000. The scheme aims to reduce maternal and infant deaths.",
        "text_hi": "जननी सुरक्षा योजना गर्भवती महिलाओं को सरकारी या मान्यताप्राप्त अस्पताल में प्रसव कराने पर नकद सहायता देती है। कम प्रदर्शन वाले राज्यों में ग्रामीण माताओं को 1400 और शहरी माताओं को 1000 रुपये मिलते हैं।",
        "eligibility_en": "All pregnant women who deliver in government or accredited private hospitals. Priority for BPL families, SC/ST women, and women above 19 years of age.",
        "eligibility_hi": "सरकारी या मान्यताप्राप्त निजी अस्पताल में प्रसव कराने वाली सभी गर्भवती महिलाएं। बीपीएल, अनुसूचित जाति/जनजाति और 19 वर्ष से अधिक उम्र की महिलाओं को प्राथमिकता।",
        "how_to_apply_en": "Register at your nearest PHC/sub-centre or government hospital during antenatal checkup. ASHA worker will assist with paperwork and cash transfer.",
        "how_to_apply_hi": "नजदीकी PHC/सब-सेंटर या सरकारी अस्पताल में प्रसव पूर्व जांच के दौरान पंजीकरण कराएं। आशा कार्यकर्ता कागजी और पैसा ट्रांसफर में मदद करेगी।",
        "documents_en": "Aadhaar card, BPL card or ration card, MCH (Mother and Child Health) card, bank account passbook linked to Aadhaar, hospital delivery proof.",
        "documents_hi": "आधार कार्ड, बीपीएल कार्ड या राशन कार्ड, MCH (मातृ और शिशु स्वास्थ्य) कार्ड, आधार से जुड़ा बैंक खाता पासबुक, अस्पताल प्रसव प्रमाण।",
        "helpline": "1800-180-1104",
        "website": "nhm.gov.in"
    },
    {
        # Source: dfpd.gov.in (PMGKAY merged into NFSA from Jan 2023)
        "scheme_id": "pm-garib-kalyan-anna",
        "section_id": "overview",
        "category": "finance",
        "name_en": "PM Garib Kalyan Anna Yojana",
        "name_hi": "प्रधान मंत्री गरीब कल्याण अन्न योजना",
        "text_en": "PM Garib Kalyan Anna Yojana gives 5 kg of free foodgrain every month to each member of Antyodaya and Priority Household families. The scheme has been extended and merged into the National Food Security Act, ensuring free grain until 2028.",
        "text_hi": "पीएम गरीब कल्याण अन्न योजना अंत्योदय और प्राथमिक घरेलू परिवार के प्रत्येक सदस्य को हर महीने 5 किलो मुफ्त अनाज देती है। यह योजना राष्ट्रीय खाद्य सुरक्षा अधिनियम में शामिल हो गई है और 2028 तक लागू है।",
        "eligibility_en": "Families with Antyodaya Anna Yojana (AAY) or Priority Household (PHH) ration cards under the National Food Security Act.",
        "eligibility_hi": "राष्ट्रीय खाद्य सुरक्षा अधिनियम के तहत अंत्योदय अन्न योजना (AAY) या प्राथमिक घरेलू (PHH) राशन कार्ड वाले परिवार।",
        "how_to_apply_en": "No separate application needed. Collect free grain every month from your Fair Price Shop (ration shop) using your ration card and Aadhaar.",
        "how_to_apply_hi": "अलग से आवेदन की जरूरत नहीं। हर महीने अपनी राशन दुकान (उचित मूल्य दुकान) से राशन कार्ड और आधार दिखाकर मुफ्त अनाज लें।",
        "documents_en": "Ration card (AAY or PHH category), Aadhaar card for biometric verification at Fair Price Shop. No other documents needed.",
        "documents_hi": "राशन कार्ड (AAY या PHH श्रेणी), राशन दुकान पर बायोमेट्रिक सत्यापन के लिए आधार कार्ड। कोई अन्य दस्तावेज नहीं चाहिए।",
        "helpline": "1967",
        "website": "dfpd.gov.in"
    },
    {
        # Source: pmjdy.gov.in
        "scheme_id": "pmjdy-jan-dhan",
        "section_id": "overview",
        "category": "finance",
        "name_en": "Pradhan Mantri Jan Dhan Yojana",
        "name_hi": "प्रधान मंत्री जन धन योजना",
        "text_en": "PM Jan Dhan gives a zero-balance bank account with a free RuPay debit card to every unbanked Indian. You also get Rs 2 lakh accident insurance, Rs 30,000 life insurance, and an Rs 10,000 overdraft facility after good account history.",
        "text_hi": "पीएम जन धन हर अनबैंक्ड भारतीय को मुफ्त RuPay डेबिट कार्ड के साथ शून्य बैलेंस बैंक खाता देती है। साथ में 2 लाख रुपये का दुर्घटना बीमा, 30,000 रुपये का जीवन बीमा और अच्छे खाते के बाद 10,000 रुपये की ओवरड्राफ्ट सुविधा मिलती है।",
        "eligibility_en": "Any Indian citizen aged 10 years and above who does not have a bank account. Documents: Aadhaar card or any officially valid document.",
        "eligibility_hi": "10 वर्ष से अधिक उम्र का कोई भी भारतीय नागरिक जिसका बैंक खाता न हो। आधार कार्ड या कोई भी सरकारी मान्य दस्तावेज चाहिए।",
        "how_to_apply_en": "Visit any bank branch or Business Correspondent (BC) outlet with Aadhaar. Account can be opened with zero balance. No minimum deposit required.",
        "how_to_apply_hi": "किसी भी बैंक शाखा या बिजनेस कॉरेस्पॉन्डेंट (BC) के पास आधार लेकर जाएं। जीरो बैलेंस पर खाता खुलता है। न्यूनतम जमा की जरूरत नहीं।",
        "documents_en": "Aadhaar card (primary). If no Aadhaar: voter ID, driving license, PAN card, passport, NREGA job card, or any government-issued ID with photograph.",
        "documents_hi": "आधार कार्ड (प्राथमिक)। आधार न होने पर: वोटर ID, ड्राइविंग लाइसेंस, पैन कार्ड, पासपोर्ट, नरेगा जॉब कार्ड, या कोई सरकारी फोटो ID।",
        "helpline": "1800-11-0001",
        "website": "pmjdy.gov.in"
    },
    {
        # Source: pmuy.gov.in / petroleum.gov.in
        "scheme_id": "pm-ujjwala-yojana",
        "section_id": "overview",
        "category": "women",
        "name_en": "Pradhan Mantri Ujjwala Yojana",
        "name_hi": "प्रधान मंत्री उज्ज्वला योजना",
        "text_en": "PM Ujjwala gives a free LPG gas connection to women from poor households. The government provides Rs 1600 financial support for the connection, a free first gas cylinder, and a free stove. This protects women from harmful indoor cooking smoke.",
        "text_hi": "पीएम उज्ज्वला गरीब घरों की महिलाओं को मुफ्त एलपीजी गैस कनेक्शन देती है। सरकार 1600 रुपये की सहायता, पहला गैस सिलेंडर और चूल्हा मुफ्त देती है। इससे महिलाएं घर के अंदर के धुएं से बचती हैं।",
        "eligibility_en": "Adult women from BPL households, SC/ST families, PMAY beneficiaries, Antyodaya families, forest/river-island dwellers, and most backward class families.",
        "eligibility_hi": "बीपीएल घरों, अनुसूचित जाति/जनजाति, पीएमएवाई लाभार्थियों, अंत्योदय परिवारों, वन/द्वीप निवासियों और अत्यंत पिछड़े वर्गों की वयस्क महिलाएं।",
        "how_to_apply_en": "Apply online at pmuy.gov.in or visit your nearest LPG distributor with Aadhaar, BPL ration card, and bank account details.",
        "how_to_apply_hi": "pmuy.gov.in पर ऑनलाइन आवेदन करें या नजदीकी LPG वितरक के पास आधार, BPL राशन कार्ड और बैंक खाता जानकारी लेकर जाएं।",
        "documents_en": "Aadhaar card of woman applicant, BPL ration card, bank account passbook, passport-size photograph, address proof, caste certificate (if SC/ST).",
        "documents_hi": "महिला आवेदक का आधार कार्ड, BPL राशन कार्ड, बैंक खाता पासबुक, पासपोर्ट साइज फोटो, पते का प्रमाण, जाति प्रमाण पत्र (SC/ST के लिए)।",
        "helpline": "1906",
        "website": "pmuy.gov.in"
    },
    {
        # Source: scholarships.gov.in
        "scheme_id": "national-scholarship-portal",
        "section_id": "overview",
        "category": "education",
        "name_en": "National Scholarship Portal",
        "name_hi": "राष्ट्रीय छात्रवृत्ति पोर्टल",
        "text_en": "The National Scholarship Portal is a single platform for all central and state government scholarships. Students from SC, ST, OBC, minority, and disabled communities can apply for pre-matric and post-matric scholarships for school and college studies.",
        "text_hi": "राष्ट्रीय छात्रवृत्ति पोर्टल केंद्र और राज्य सरकार की सभी छात्रवृत्तियों के लिए एक ही मंच है। एससी, एसटी, ओबीसी, अल्पसंख्यक और दिव्यांग समुदाय के छात्र स्कूल और कॉलेज की पढ़ाई के लिए प्री-मैट्रिक और पोस्ट-मैट्रिक छात्रवृत्ति के लिए आवेदन कर सकते हैं।",
        "eligibility_en": "Students from SC, ST, OBC, minority communities, and students with disabilities enrolled in schools or colleges. Income limits vary by scholarship.",
        "eligibility_hi": "एससी, एसटी, ओबीसी, अल्पसंख्यक समुदाय और दिव्यांग छात्र जो स्कूल या कॉलेज में पढ़ रहे हों। आय सीमा छात्रवृत्ति के अनुसार अलग-अलग है।",
        "how_to_apply_en": "Register on scholarships.gov.in with Aadhaar and generate a One-Time Registration (OTR) number. Apply before the deadline with academic and bank documents.",
        "how_to_apply_hi": "scholarships.gov.in पर आधार से पंजीकरण करें और One-Time Registration (OTR) नंबर बनाएं। अंतिम तिथि से पहले शैक्षिक और बैंक दस्तावेजों के साथ आवेदन करें।",
        "documents_en": "Aadhaar card, income certificate, caste certificate (SC/ST/OBC/minority), disability certificate (if applicable), previous year marksheet, current enrollment proof, bank account passbook, passport-size photograph.",
        "documents_hi": "आधार कार्ड, आय प्रमाण पत्र, जाति प्रमाण पत्र (SC/ST/OBC/अल्पसंख्यक), दिव्यांग प्रमाण पत्र (यदि लागू), पिछले वर्ष की मार्कशीट, वर्तमान नामांकन प्रमाण, बैंक खाता पासबुक, पासपोर्ट साइज फोटो।",
        "helpline": "0120-6619540",
        "website": "scholarships.gov.in"
    },
    # ── 17 new schemes (sources: official GOI portals) ───────────────────────
    {
        # Source: soilhealth.dac.gov.in
        "scheme_id": "soil-health-card",
        "section_id": "overview",
        "category": "agriculture",
        "name_en": "Soil Health Card Scheme",
        "name_hi": "मृदा स्वास्थ्य कार्ड योजना",
        "text_en": "Soil Health Card gives every farmer a report on the health of their soil. It tells you which nutrients are present and which fertilizers to use. Cards are issued every 2 years so you can improve your soil and get better crops.",
        "text_hi": "मृदा स्वास्थ्य कार्ड योजना में हर किसान को उसकी मिट्टी की जांच रिपोर्ट मिलती है। इसमें बताया जाता है कि मिट्टी में कौन से पोषक तत्व हैं और कौन सी खाद डालनी चाहिए। हर 2 साल में नया कार्ड मिलता है जिससे फसल बेहतर होती है।",
        "eligibility_en": "All farmers across India. Free of cost. Available through Agriculture Department and Krishi Vigyan Kendras.",
        "eligibility_hi": "भारत के सभी किसान। पूरी तरह मुफ्त। कृषि विभाग और कृषि विज्ञान केंद्रों के माध्यम से उपलब्ध।",
        "how_to_apply_en": "Contact your local Agriculture Department office or Krishi Vigyan Kendra. Soil samples will be collected from your farm for testing.",
        "how_to_apply_hi": "स्थानीय कृषि विभाग कार्यालय या कृषि विज्ञान केंद्र से संपर्क करें। आपके खेत से मिट्टी के नमूने लेकर जांच की जाएगी।",
        "documents_en": "Aadhaar card and land details. No formal application needed - contact Agriculture Department or Krishi Vigyan Kendra directly.",
        "documents_hi": "आधार कार्ड और जमीन की जानकारी। औपचारिक आवेदन की जरूरत नहीं - सीधे कृषि विभाग या KVK से संपर्क करें।",
        "helpline": "1800-180-1551",
        "website": "soilhealth.dac.gov.in"
    },
    {
        # Source: mdm.nic.in (now PM POSHAN under education.gov.in)
        "scheme_id": "pm-poshan-mid-day-meal",
        "section_id": "overview",
        "category": "education",
        "name_en": "PM POSHAN (Mid-Day Meal)",
        "name_hi": "पीएम पोषण (मध्याह्न भोजन योजना)",
        "text_en": "PM POSHAN gives free cooked meals to children in government and aided schools from class 1 to 8. Primary children get 450 calories and upper-primary get 700 calories per meal. It improves nutrition and school attendance.",
        "text_hi": "पीएम पोषण योजना सरकारी और सहायता प्राप्त स्कूलों में कक्षा 1 से 8 तक के बच्चों को मुफ्त पका हुआ भोजन देती है। प्राथमिक बच्चों को 450 कैलोरी और उच्च प्राथमिक को 700 कैलोरी मिलती है। इससे पोषण और स्कूल उपस्थिति बढ़ती है।",
        "eligibility_en": "All children enrolled in government, government-aided, and local body schools from class 1 to 8. No application needed.",
        "eligibility_hi": "सरकारी, सरकारी सहायता प्राप्त और स्थानीय निकाय के स्कूलों में कक्षा 1 से 8 तक पढ़ने वाले सभी बच्चे। कोई आवेदन ज़रूरी नहीं।",
        "how_to_apply_en": "No application required. Meals are served automatically in eligible schools. Contact school headmaster for details.",
        "how_to_apply_hi": "आवेदन की जरूरत नहीं। पात्र स्कूलों में स्वचालित रूप से भोजन परोसा जाता है। जानकारी के लिए स्कूल प्रधानाध्यापक से संपर्क करें।",
        "documents_en": "No documents needed for students. Enrollment in government or government-aided school from class 1 to 8 is sufficient.",
        "documents_hi": "छात्रों के लिए कोई दस्तावेज नहीं चाहिए। सरकारी या सरकारी सहायता प्राप्त स्कूल में कक्षा 1 से 8 में नामांकन पर्याप्त है।",
        "helpline": "1800-180-5727",
        "website": "pmposhan.education.gov.in"
    },
    {
        # Source: wcd.nic.in (Mahila Samman Savings Certificate via India Post / banks)
        "scheme_id": "mahila-samman-savings",
        "section_id": "overview",
        "category": "women",
        "name_en": "Mahila Samman Savings Certificate",
        "name_hi": "महिला सम्मान बचत प्रमाणपत्र",
        "text_en": "Mahila Samman Savings Certificate is a 2-year savings scheme for women and girls. You can deposit up to Rs 2 lakh and get 7.5% interest per year. Partial withdrawal is allowed after 1 year. Available at post offices and banks.",
        "text_hi": "महिला सम्मान बचत प्रमाणपत्र महिलाओं और लड़कियों के लिए 2 साल की बचत योजना है। 2 लाख रुपये तक जमा पर 7.5% सालाना ब्याज मिलता है। 1 साल बाद आंशिक निकासी हो सकती है। डाकघर और बैंकों में उपलब्ध है।",
        "eligibility_en": "Any woman or girl in India. Account can be opened by parent/guardian for a minor girl. One account per person per institution.",
        "eligibility_hi": "भारत की कोई भी महिला या लड़की। नाबालिग लड़की के लिए माता-पिता/अभिभावक खाता खुलवा सकते हैं। एक संस्था में एक व्यक्ति का एक खाता।",
        "how_to_apply_en": "Visit any post office or authorized bank with Aadhaar, PAN card, and passport-size photo. Minimum deposit Rs 1000.",
        "how_to_apply_hi": "किसी भी पोस्ट ऑफिस या अधिकृत बैंक में आधार, पैन कार्ड और पासपोर्ट साइज फोटो लेकर जाएं। न्यूनतम जमा 1000 रुपये।",
        "documents_en": "Aadhaar card, PAN card, passport-size photograph, address proof. For minor girl: birth certificate and parent/guardian documents.",
        "documents_hi": "आधार कार्ड, पैन कार्ड, पासपोर्ट साइज फोटो, पते का प्रमाण। नाबालिग लड़की के लिए: जन्म प्रमाण पत्र और माता-पिता/अभिभावक के दस्तावेज।",
        "helpline": "1800-266-6868",
        "website": "indiapost.gov.in"
    },
    {
        # Source: pmkvy.skillsindia.gov.in
        "scheme_id": "pm-kaushal-vikas",
        "section_id": "overview",
        "category": "education",
        "name_en": "Pradhan Mantri Kaushal Vikas Yojana",
        "name_hi": "प्रधान मंत्री कौशल विकास योजना",
        "text_en": "PM Kaushal Vikas gives free skill training and certification to Indian youth. Training is given in trades like electrician, plumber, beautician, computer skills, and welding. Trainees also get placement support after completing the course.",
        "text_hi": "पीएम कौशल विकास योजना भारतीय युवाओं को मुफ्त कौशल प्रशिक्षण और प्रमाणपत्र देती है। इलेक्ट्रीशियन, प्लंबर, ब्यूटीशियन, कंप्यूटर और वेल्डिंग जैसे कामों में ट्रेनिंग मिलती है। कोर्स पूरा करने पर नौकरी लगाने में भी मदद मिलती है।",
        "eligibility_en": "Indian youth who are school or college dropouts or unemployed. Training centres (PMKVY TCs) available across districts.",
        "eligibility_hi": "भारतीय युवा जो स्कूल/कॉलेज छोड़ चुके हों या बेरोज़गार हों। हर जिले में पीएमकेवीवाई प्रशिक्षण केंद्र उपलब्ध हैं।",
        "how_to_apply_en": "Visit the nearest PMKVY Training Centre or register at skillindia.gov.in. Carry Aadhaar and educational documents.",
        "how_to_apply_hi": "नजदीकी PMKVY प्रशिक्षण केंद्र पर जाएं या skillindia.gov.in पर पंजीकरण करें। आधार और शैक्षिक दस्तावेज लेकर जाएं।",
        "documents_en": "Aadhaar card, educational certificates (if any), bank account details, passport-size photographs, mobile number.",
        "documents_hi": "आधार कार्ड, शैक्षिक प्रमाण पत्र (यदि हों), बैंक खाता जानकारी, पासपोर्ट साइज फोटो, मोबाइल नंबर।",
        "helpline": "1800-123-9626",
        "website": "pmkvyofficial.org"
    },
    {
        # Source: pmsby.gov.in / jansuraksha.gov.in
        "scheme_id": "pm-suraksha-bima",
        "section_id": "overview",
        "category": "finance",
        "name_en": "Pradhan Mantri Suraksha Bima Yojana",
        "name_hi": "प्रधान मंत्री सुरक्षा बीमा योजना",
        "text_en": "PM Suraksha Bima gives accidental death and disability insurance of Rs 2 lakh for just Rs 20 per year. If you die or become fully disabled in an accident, your family gets Rs 2 lakh. For partial disability, Rs 1 lakh is paid.",
        "text_hi": "पीएम सुरक्षा बीमा योजना में सिर्फ 20 रुपये सालाना में 2 लाख रुपये का दुर्घटना बीमा मिलता है। दुर्घटना में मृत्यु या पूर्ण विकलांगता पर परिवार को 2 लाख और आंशिक विकलांगता पर 1 लाख रुपये मिलते हैं।",
        "eligibility_en": "Indian citizens aged 18–70 years with a savings bank account. Premium of Rs 20 is auto-debited from bank account yearly.",
        "eligibility_hi": "18 से 70 वर्ष के भारतीय नागरिक जिनके पास बचत बैंक खाता हो। 20 रुपये का प्रीमियम हर साल खाते से अपने आप कट जाता है।",
        "how_to_apply_en": "Apply at your bank branch, or through net banking or mobile banking. Fill a one-page form and give consent for auto-debit.",
        "how_to_apply_hi": "बैंक शाखा में जाएं, या नेट बैंकिंग/मोबाइल बैंकिंग से आवेदन करें। एक पेज का फॉर्म भरें और ऑटो-डेबिट की सहमति दें।",
        "documents_en": "Savings bank account, Aadhaar card. One-page enrollment form signed. No medical examination needed.",
        "documents_hi": "बचत बैंक खाता, आधार कार्ड। एक पेज का नामांकन फॉर्म हस्ताक्षरित। कोई चिकित्सा जांच नहीं चाहिए।",
        "helpline": "1800-180-1111",
        "website": "jansuraksha.gov.in"
    },
    {
        # Source: pmjjby.gov.in / jansuraksha.gov.in
        "scheme_id": "pm-jeevan-jyoti-bima",
        "section_id": "overview",
        "category": "finance",
        "name_en": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "name_hi": "प्रधान मंत्री जीवन ज्योति बीमा योजना",
        "text_en": "PM Jeevan Jyoti gives life insurance of Rs 2 lakh for Rs 436 per year. If the insured person dies for any reason, the family gets Rs 2 lakh. The premium is auto-debited from the bank account once a year.",
        "text_hi": "पीएम जीवन ज्योति बीमा में सिर्फ 436 रुपये सालाना में 2 लाख रुपये का जीवन बीमा मिलता है। बीमित व्यक्ति की किसी भी कारण से मृत्यु होने पर परिवार को 2 लाख रुपये मिलते हैं। प्रीमियम बैंक खाते से साल में एक बार कटता है।",
        "eligibility_en": "Indian citizens aged 18–55 years with a savings bank account. Must agree to auto-debit of premium.",
        "eligibility_hi": "18 से 55 वर्ष के भारतीय नागरिक जिनके पास बचत बैंक खाता हो। प्रीमियम ऑटो-डेबिट की सहमति ज़रूरी है।",
        "how_to_apply_en": "Apply at your bank branch, or through net banking or mobile banking. One-page form and auto-debit consent needed.",
        "how_to_apply_hi": "बैंक शाखा में जाएं, या नेट बैंकिंग/मोबाइल बैंकिंग से आवेदन करें। एक पेज का फॉर्म और ऑटो-डेबिट सहमति जरूरी।",
        "documents_en": "Savings bank account, Aadhaar card, one-page enrollment form with auto-debit consent. No medical examination required.",
        "documents_hi": "बचत बैंक खाता, आधार कार्ड, ऑटो-डेबिट सहमति वाला नामांकन फॉर्म। कोई चिकित्सा जांच जरूरी नहीं।",
        "helpline": "1800-180-1111",
        "website": "jansuraksha.gov.in"
    },
    {
        # Source: standupmitra.in / sidbi.in
        "scheme_id": "stand-up-india",
        "section_id": "overview",
        "category": "finance",
        "name_en": "Stand Up India",
        "name_hi": "स्टैंड अप इंडिया",
        "text_en": "Stand Up India gives bank loans between Rs 10 lakh and Rs 1 crore to SC/ST and women entrepreneurs to start a new business in manufacturing, services, or trading. At least one SC/ST and one woman borrower per bank branch.",
        "text_hi": "स्टैंड अप इंडिया अनुसूचित जाति/जनजाति और महिला उद्यमियों को नया व्यवसाय शुरू करने के लिए 10 लाख से 1 करोड़ रुपये तक का बैंक ऋण देती है। हर बैंक शाखा से कम से कम एक एससी/एसटी और एक महिला को कर्ज मिलता है।",
        "eligibility_en": "SC/ST and/or women entrepreneurs aged 18+ setting up a first-time greenfield enterprise in manufacturing, services, or trading.",
        "eligibility_hi": "अनुसूचित जाति/जनजाति और/या 18 वर्ष से अधिक उम्र की महिला उद्यमी जो पहली बार विनिर्माण, सेवा या व्यापार में नया उद्यम शुरू कर रही हों।",
        "how_to_apply_en": "Apply online at standupmitra.in or visit any scheduled commercial bank branch. Carry Aadhaar, project report, and caste/identity documents.",
        "how_to_apply_hi": "standupmitra.in पर ऑनलाइन आवेदन करें या किसी भी अनुसूचित वाणिज्यिक बैंक शाखा में जाएं। आधार, प्रोजेक्ट रिपोर्ट और जाति/पहचान दस्तावेज लेकर जाएं।",
        "documents_en": "Aadhaar card, PAN card, caste certificate (for SC/ST), project report/business plan, address proof, bank account details, identity proof, passport-size photographs.",
        "documents_hi": "आधार कार्ड, पैन कार्ड, जाति प्रमाण पत्र (SC/ST के लिए), प्रोजेक्ट रिपोर्ट/व्यापार योजना, पते का प्रमाण, बैंक खाता जानकारी, पहचान पत्र, पासपोर्ट साइज फोटो।",
        "helpline": "1800-180-1111",
        "website": "standupmitra.in"
    },
    {
        # Source: pmindia.gov.in / niti.gov.in (Matru Vandana section)
        "scheme_id": "pm-matru-vandana",
        "section_id": "overview",
        "category": "women",
        "name_en": "Pradhan Mantri Matru Vandana Yojana",
        "name_hi": "प्रधान मंत्री मातृ वंदना योजना",
        "text_en": "PM Matru Vandana gives Rs 5000 cash to pregnant women for their first child, directly in their bank account in 3 instalments. For the second child (if girl), Rs 6000 is given. It supports health and nutrition during pregnancy.",
        "text_hi": "पीएम मातृ वंदना योजना पहली संतान के लिए गर्भवती महिलाओं को 5000 रुपये तीन किस्तों में सीधे बैंक खाते में देती है। दूसरी संतान अगर बेटी हो तो 6000 रुपये मिलते हैं। यह गर्भावस्था में स्वास्थ्य और पोषण के लिए मदद करती है।",
        "eligibility_en": "Pregnant women and lactating mothers for first live birth. For second child benefit, the child must be a girl.",
        "eligibility_hi": "पहले जीवित बच्चे के लिए गर्भवती और स्तनपान कराने वाली माताएं। दूसरे बच्चे के लिए लाभ तभी मिलेगा जब बच्ची हो।",
        "how_to_apply_en": "Register at Anganwadi centre or approved health facility. Carry Aadhaar, bank passbook, and MCP card.",
        "how_to_apply_hi": "आंगनवाड़ी केंद्र या मान्यताप्राप्त स्वास्थ्य केंद्र में पंजीकरण कराएं। आधार, बैंक पासबुक और MCP कार्ड लेकर जाएं।",
        "documents_en": "Aadhaar card, bank account passbook linked to Aadhaar, MCP (Mother and Child Protection) card, pregnancy registration proof, hospital/ANM delivery record.",
        "documents_hi": "आधार कार्ड, आधार से जुड़ा बैंक खाता पासबुक, MCP (मातृ एवं शिशु सुरक्षा) कार्ड, गर्भावस्था पंजीकरण प्रमाण, अस्पताल/ANM प्रसव रिकॉर्ड।",
        "helpline": "181",
        "website": "wcd.nic.in"
    },
    {
        # Source: dbtbharat.gov.in / nfbs.gov.in (under MoRD)
        "scheme_id": "national-family-benefit",
        "section_id": "overview",
        "category": "finance",
        "name_en": "National Family Benefit Scheme",
        "name_hi": "राष्ट्रीय परिवार लाभ योजना",
        "text_en": "National Family Benefit Scheme gives Rs 20,000 one-time assistance to the family of a deceased primary breadwinner. The payment goes to the surviving member of the BPL household within 4 weeks of application.",
        "text_hi": "राष्ट्रीय परिवार लाभ योजना में परिवार के मुख्य कमाने वाले की मृत्यु होने पर बीपीएल परिवार को 20,000 रुपये की एकमुश्त सहायता मिलती है। आवेदन के 4 सप्ताह के भीतर जीवित सदस्य को भुगतान किया जाता है।",
        "eligibility_en": "BPL families where the primary breadwinner (18-60 years) has died. Both rural and urban families are eligible.",
        "eligibility_hi": "बीपीएल परिवार जिनके मुख्य कमाने वाले (18-60 वर्ष) की मृत्यु हो गई हो। ग्रामीण और शहरी दोनों परिवार पात्र हैं।",
        "how_to_apply_en": "Apply at district social welfare office or through NSAP portal. Carry death certificate, BPL card, Aadhaar, and bank details.",
        "how_to_apply_hi": "जिला समाज कल्याण कार्यालय में या NSAP पोर्टल पर आवेदन करें। मृत्यु प्रमाण पत्र, बीपीएल कार्ड, आधार और बैंक जानकारी लेकर जाएं।",
        "documents_en": "Death certificate of breadwinner, BPL card, Aadhaar card of applicant and deceased, bank account passbook, age proof of deceased, FIR copy (if applicable).",
        "documents_hi": "कमाने वाले का मृत्यु प्रमाण पत्र, बीपीएल कार्ड, आवेदक और मृतक का आधार कार्ड, बैंक खाता पासबुक, मृतक की आयु प्रमाण, FIR कॉपी (यदि लागू)।",
        "helpline": "1800-111-555",
        "website": "nsap.nic.in"
    },
    {
        # Source: samagra.gov.in / education.gov.in
        "scheme_id": "samagra-shiksha",
        "section_id": "overview",
        "category": "education",
        "name_en": "Samagra Shiksha Abhiyan",
        "name_hi": "समग्र शिक्षा अभियान",
        "text_en": "Samagra Shiksha is an integrated scheme for school education from pre-primary to class 12. It provides free textbooks, uniforms, school infrastructure, teacher training, and transport support for children with disabilities.",
        "text_hi": "समग्र शिक्षा अभियान प्री-प्राइमरी से कक्षा 12 तक की स्कूली शिक्षा के लिए एकीकृत योजना है। इसमें मुफ्त किताबें, वर्दी, स्कूल का बुनियादी ढांचा, शिक्षक प्रशिक्षण और दिव्यांग बच्चों के लिए परिवहन सहायता दी जाती है।",
        "eligibility_en": "All children in government and government-aided schools from pre-primary to class 12. Special focus on girls, SC/ST, and disabled children.",
        "eligibility_hi": "सरकारी और सरकारी सहायता प्राप्त स्कूलों में प्री-प्राइमरी से कक्षा 12 तक पढ़ने वाले सभी बच्चे। लड़कियों, एससी/एसटी और दिव्यांग बच्चों पर विशेष ध्यान।",
        "how_to_apply_en": "No application needed for students. Benefits flow through schools. Contact the school headmaster or District Education Office.",
        "how_to_apply_hi": "छात्रों के लिए आवेदन की जरूरत नहीं। लाभ स्कूलों के माध्यम से मिलते हैं। स्कूल प्रधानाध्यापक या जिला शिक्षा कार्यालय से संपर्क करें।",
        "documents_en": "No documents needed for students. School enrollment is sufficient. Schools apply through District Education Office for funding.",
        "documents_hi": "छात्रों के लिए कोई दस्तावेज नहीं। स्कूल में नामांकन पर्याप्त है। स्कूल जिला शिक्षा कार्यालय से फंडिंग के लिए आवेदन करते हैं।",
        "helpline": "1800-111-001",
        "website": "samagra.education.gov.in"
    },
    {
        # Source: nhm.gov.in / rch.nhm.gov.in
        "scheme_id": "rashtriya-bal-swasthya",
        "section_id": "overview",
        "category": "health",
        "name_en": "Rashtriya Bal Swasthya Karyakram",
        "name_hi": "राष्ट्रीय बाल स्वास्थ्य कार्यक्रम",
        "text_en": "RBSK provides free health screening of children from birth to 18 years for 4 Ds: Defects at birth, Diseases, Deficiencies, and Development delays. Mobile health teams visit schools and Anganwadis. Free treatment is provided at district hospitals.",
        "text_hi": "आरबीएसके जन्म से 18 साल तक के बच्चों की मुफ्त स्वास्थ्य जांच करता है – जन्मजात दोष, बीमारियां, कमियां और विकास में देरी। मोबाइल स्वास्थ्य दल स्कूलों और आंगनवाड़ियों में आते हैं। जिला अस्पतालों में मुफ्त इलाज मिलता है।",
        "eligibility_en": "All children from newborn to 18 years. Screening at government schools, Anganwadi centres, and at birth in public health facilities.",
        "eligibility_hi": "नवजात से 18 वर्ष तक के सभी बच्चे। सरकारी स्कूलों, आंगनवाड़ी केंद्रों और सरकारी अस्पतालों में जन्म के समय जांच होती है।",
        "how_to_apply_en": "No application needed. RBSK mobile health teams visit schools and Anganwadis. For referral, contact nearest PHC or district hospital.",
        "how_to_apply_hi": "आवेदन की जरूरत नहीं। RBSK मोबाइल स्वास्थ्य दल स्कूलों और आंगनवाड़ियों में आते हैं। रेफरल के लिए नजदीकी PHC या जिला अस्पताल से संपर्क करें।",
        "documents_en": "No documents needed. Free screening at schools and Anganwadis. For treatment referral: child's Aadhaar or birth certificate.",
        "documents_hi": "कोई दस्तावेज नहीं चाहिए। स्कूलों और आंगनवाड़ियों में मुफ्त जांच। इलाज रेफरल के लिए: बच्चे का आधार या जन्म प्रमाण पत्र।",
        "helpline": "1800-180-1104",
        "website": "nhm.gov.in"
    },
    {
        # Source: amrut.gov.in / mohua.gov.in
        "scheme_id": "pm-saubhagya",
        "section_id": "overview",
        "category": "housing",
        "name_en": "Saubhagya - Sahaj Bijli Har Ghar Yojana",
        "name_hi": "सौभाग्य - सहज बिजली हर घर योजना",
        "text_en": "Saubhagya scheme provides free electricity connections to all remaining un-electrified households in rural and urban areas. BPL households get the connection free, and APL households pay Rs 500 in 10 monthly instalments.",
        "text_hi": "सौभाग्य योजना ग्रामीण और शहरी क्षेत्रों में बिना बिजली वाले सभी घरों को मुफ्त बिजली कनेक्शन देती है। बीपीएल घरों को मुफ्त कनेक्शन मिलता है और एपीएल घरों को 500 रुपये 10 मासिक किस्तों में देने होते हैं।",
        "eligibility_en": "All un-electrified households in India. Priority for BPL families, SC/ST households, and those in remote areas.",
        "eligibility_hi": "भारत के सभी बिना बिजली वाले घर। बीपीएल परिवारों, अनुसूचित जाति/जनजाति और दूरदराज के क्षेत्रों को प्राथमिकता।",
        "how_to_apply_en": "Contact your local electricity distribution company (DISCOM) or gram panchayat. Carry Aadhaar and BPL card if applicable.",
        "how_to_apply_hi": "स्थानीय बिजली वितरण कंपनी (DISCOM) या ग्राम पंचायत से संपर्क करें। आधार और BPL कार्ड (यदि लागू) लेकर जाएं।",
        "documents_en": "Aadhaar card, BPL card (if applicable), address proof. No other formalities for BPL households.",
        "documents_hi": "आधार कार्ड, BPL कार्ड (यदि लागू), पते का प्रमाण। BPL परिवारों के लिए कोई अन्य औपचारिकता नहीं।",
        "helpline": "1912",
        "website": "saubhagya.gov.in"
    },
    {
        # Source: swachhbharatmission.gov.in
        "scheme_id": "swachh-bharat-gramin",
        "section_id": "overview",
        "category": "housing",
        "name_en": "Swachh Bharat Mission (Gramin)",
        "name_hi": "स्वच्छ भारत मिशन (ग्रामीण)",
        "text_en": "Swachh Bharat Gramin gives Rs 12,000 to rural families for building household toilets. It also focuses on solid and liquid waste management in villages. The mission aims to make all villages Open Defecation Free (ODF).",
        "text_hi": "स्वच्छ भारत ग्रामीण योजना ग्रामीण परिवारों को घर में शौचालय बनाने के लिए 12,000 रुपये देती है। गांवों में ठोस और तरल कचरा प्रबंधन पर भी ध्यान दिया जाता है। मिशन का लक्ष्य सभी गांवों को खुले में शौच मुक्त बनाना है।",
        "eligibility_en": "Rural households without a toilet. Priority for BPL families, SC/ST, small and marginal farmers, landless labourers, and women-headed households.",
        "eligibility_hi": "शौचालय नहीं होने वाले ग्रामीण घर। बीपीएल, अनुसूचित जाति/जनजाति, छोटे किसान, भूमिहीन मज़दूर और महिला प्रधान परिवारों को प्राथमिकता।",
        "how_to_apply_en": "Apply at gram panchayat office or Block Development Office. Carry Aadhaar, BPL card, and bank account details.",
        "how_to_apply_hi": "ग्राम पंचायत कार्यालय या खंड विकास कार्यालय में आवेदन करें। आधार, BPL कार्ड और बैंक खाता जानकारी लेकर जाएं।",
        "documents_en": "Aadhaar card, BPL card or ration card, bank account passbook, photograph of the household (showing no toilet), address proof.",
        "documents_hi": "आधार कार्ड, BPL कार्ड या राशन कार्ड, बैंक खाता पासबुक, घर की फोटो (शौचालय न होने का प्रमाण), पते का प्रमाण।",
        "helpline": "1969",
        "website": "swachhbharatmission.gov.in"
    },
    {
        # Source: labour.gov.in / epfindia.gov.in
        "scheme_id": "pm-shram-yogi-mandhan",
        "section_id": "overview",
        "category": "finance",
        "name_en": "PM Shram Yogi Mandhan Yojana",
        "name_hi": "प्रधान मंत्री श्रम योगी मानधन योजना",
        "text_en": "PM Shram Yogi Mandhan gives Rs 3000 per month pension after age 60 to unorganised sector workers. Workers contribute Rs 55 to Rs 200 per month depending on their age, and the government matches the same amount.",
        "text_hi": "पीएम श्रम योगी मानधन असंगठित क्षेत्र के कामगारों को 60 साल के बाद हर महीने 3000 रुपये पेंशन देती है। कामगार उम्र के अनुसार 55 से 200 रुपये मासिक देते हैं और सरकार भी उतनी ही राशि जमा करती है।",
        "eligibility_en": "Unorganised workers aged 18-40 with monthly income up to Rs 15,000. Not for EPFO/ESIC/NPS members or income tax payers.",
        "eligibility_hi": "18 से 40 वर्ष के असंगठित कामगार जिनकी मासिक आय 15,000 रुपये तक हो। ईपीएफओ/ईएसआईसी/एनपीएस सदस्य और आयकरदाता पात्र नहीं हैं।",
        "how_to_apply_en": "Visit nearest CSC centre with Aadhaar and savings bank account. CSC operator will register you. Monthly contribution auto-debited from bank.",
        "how_to_apply_hi": "नजदीकी CSC केंद्र में आधार और बचत बैंक खाता लेकर जाएं। CSC ऑपरेटर पंजीकरण करेगा। मासिक योगदान बैंक से अपने आप कटेगा।",
        "documents_en": "Aadhaar card, savings bank account details, mobile number. No other documents required.",
        "documents_hi": "आधार कार्ड, बचत बैंक खाता जानकारी, मोबाइल नंबर। कोई अन्य दस्तावेज जरूरी नहीं।",
        "helpline": "1800-267-6888",
        "website": "maandhan.in"
    },
    {
        # Source: pmvishwakarma.gov.in
        "scheme_id": "pm-vishwakarma",
        "section_id": "overview",
        "category": "finance",
        "name_en": "PM Vishwakarma Yojana",
        "name_hi": "पीएम विश्वकर्मा योजना",
        "text_en": "PM Vishwakarma supports traditional artisans and craftspeople working with their hands. It gives free skill training, toolkit, up to Rs 3 lakh collateral-free loan at 5% interest, and digital payment incentives. Covers 18 trades like carpenter, goldsmith, potter, blacksmith.",
        "text_hi": "पीएम विश्वकर्मा पारंपरिक कारीगरों और शिल्पकारों को मदद करती है। मुफ्त कौशल प्रशिक्षण, औज़ार, 5% ब्याज पर 3 लाख रुपये तक का बिना गारंटी ऋण और डिजिटल भुगतान प्रोत्साहन मिलता है। बढ़ई, सुनार, कुम्हार, लोहार समेत 18 व्यापार शामिल हैं।",
        "eligibility_en": "Traditional artisans and craftspeople working with hands and tools in 18 notified trades. Must be 18+ and not a government employee.",
        "eligibility_hi": "18 अधिसूचित व्यापारों में हाथ और औज़ारों से काम करने वाले पारंपरिक कारीगर और शिल्पकार। 18 वर्ष से अधिक और सरकारी कर्मचारी न हों।",
        "how_to_apply_en": "Register at pmvishwakarma.gov.in with Aadhaar and mobile. Gram Panchayat/ULB verification needed. Then apply for training and loans.",
        "how_to_apply_hi": "pmvishwakarma.gov.in पर आधार और मोबाइल से पंजीकरण करें। ग्राम पंचायत/शहरी निकाय से सत्यापन जरूरी। उसके बाद प्रशिक्षण और लोन के लिए आवेदन करें।",
        "documents_en": "Aadhaar card, mobile number, bank account details, caste certificate (if applicable), trade-related identity proof, passport-size photographs.",
        "documents_hi": "आधार कार्ड, मोबाइल नंबर, बैंक खाता जानकारी, जाति प्रमाण पत्र (यदि लागू), व्यापार से संबंधित पहचान, पासपोर्ट साइज फोटो।",
        "helpline": "1800-599-0094",
        "website": "pmvishwakarma.gov.in"
    },
    {
        # Source: nhmmp.gov.in / nhm.gov.in (JSSK under NHM)
        "scheme_id": "janani-shishu-suraksha",
        "section_id": "overview",
        "category": "health",
        "name_en": "Janani Shishu Suraksha Karyakram",
        "name_hi": "जननी शिशु सुरक्षा कार्यक्रम",
        "text_en": "JSSK provides free delivery services, C-section, medicines, diagnostics, blood, diet, and transport from home to hospital and back for pregnant women. Sick newborns up to 30 days also get free treatment in government hospitals.",
        "text_hi": "जेएसएसके गर्भवती महिलाओं को सरकारी अस्पतालों में मुफ्त प्रसव, सी-सेक्शन, दवाइयां, जांच, रक्त, भोजन और घर से अस्पताल तक मुफ्त परिवहन देता है। 30 दिन तक के बीमार नवजात को भी मुफ्त इलाज मिलता है।",
        "eligibility_en": "All pregnant women delivering in government health facilities and sick newborns up to 30 days. No income or BPL criteria.",
        "eligibility_hi": "सरकारी स्वास्थ्य संस्थानों में प्रसव कराने वाली सभी गर्भवती महिलाएं और 30 दिन तक के बीमार नवजात शिशु। कोई आय या बीपीएल शर्त नहीं।",
        "how_to_apply_en": "Go directly to any government hospital for delivery. All services are cashless. ASHA worker will help with transport and registration.",
        "how_to_apply_hi": "प्रसव के लिए सीधे किसी सरकारी अस्पताल में जाएं। सभी सेवाएं कैशलेस हैं। आशा कार्यकर्ता परिवहन और पंजीकरण में मदद करेगी।",
        "documents_en": "Aadhaar card or any government ID, pregnancy registration proof (if available). No documents mandatory - services cannot be denied.",
        "documents_hi": "आधार कार्ड या कोई सरकारी पहचान, गर्भावस्था पंजीकरण प्रमाण (यदि हो)। कोई दस्तावेज अनिवार्य नहीं - सेवा से मना नहीं किया जा सकता।",
        "helpline": "1800-180-1104",
        "website": "nhm.gov.in"
    },
    {
        # Source: vikaspedia.in / jaldoot.gov.in / mowr.gov.in
        "scheme_id": "pm-krishi-sinchai",
        "section_id": "overview",
        "category": "agriculture",
        "name_en": "Pradhan Mantri Krishi Sinchai Yojana",
        "name_hi": "प्रधान मंत्री कृषि सिंचाई योजना",
        "text_en": "PM Krishi Sinchai provides subsidies for drip irrigation, sprinkler systems, and micro-irrigation to help farmers use water efficiently. Subsidy of 55% for small and marginal farmers and 45% for others is given on micro-irrigation equipment.",
        "text_hi": "पीएम कृषि सिंचाई योजना किसानों को ड्रिप सिंचाई, स्प्रिंकलर और सूक्ष्म सिंचाई उपकरणों पर सब्सिडी देती है ताकि पानी की बचत हो। छोटे और सीमांत किसानों को 55% और अन्य किसानों को 45% सब्सिडी मिलती है।",
        "eligibility_en": "All farmers with own or leased agricultural land. Priority for small and marginal farmers, SC/ST farmers, and women farmers.",
        "eligibility_hi": "अपनी या पट्टे की कृषि भूमि वाले सभी किसान। छोटे और सीमांत किसानों, अनुसूचित जाति/जनजाति और महिला किसानों को प्राथमिकता।",
        "how_to_apply_en": "Apply through the State Agriculture/Horticulture Department or register at pmksy.gov.in. Carry land documents, Aadhaar, and bank details.",
        "how_to_apply_hi": "राज्य कृषि/उद्यानिकी विभाग से आवेदन करें या pmksy.gov.in पर पंजीकरण करें। जमीन के कागजात, आधार और बैंक जानकारी लेकर जाएं।",
        "documents_en": "Aadhaar card, land ownership or lease documents, bank account passbook, quotation for irrigation equipment, passport-size photographs.",
        "documents_hi": "आधार कार्ड, जमीन स्वामित्व या पट्टे के कागजात, बैंक खाता पासबुक, सिंचाई उपकरण का कोटेशन, पासपोर्ट साइज फोटो।",
        "helpline": "1800-180-1551",
        "website": "pmksy.gov.in"
    },
]

# ── FAQ & detailed sections for each scheme ───────────────────────────────
# Stored as separate knowledge items (section_id="faqs") for better
# vector-search matching when callers ask specific questions.
EXTRA_SECTIONS = [
    # ── PM-Kisan FAQs ─────────────────────────────────────────────────────
    {
        "scheme_id": "pm-kisan",
        "section_id": "faqs",
        "category": "agriculture",
        "name_en": "PM-Kisan FAQs",
        "name_hi": "पीएम किसान अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM-Kisan Samman Nidhi:\n\n"
            "Q: How much money do I get under PM-Kisan?\n"
            "A: You get Rs 6,000 per year, paid in 3 equal installments of Rs 2,000 each. Installments come every 4 months directly to your bank account linked with Aadhaar.\n\n"
            "Q: What documents are needed for PM-Kisan?\n"
            "A: Aadhaar card, bank account passbook linked to Aadhaar, land ownership records (khatauni/khasra), and mobile number. Aadhaar-bank linking is mandatory.\n\n"
            "Q: How to check PM-Kisan payment status?\n"
            "A: Visit pmkisan.gov.in and click 'Beneficiary Status'. Enter your Aadhaar number, mobile number, or account number to check. You can also call helpline 155261 or 011-24300606.\n\n"
            "Q: When do PM-Kisan installments come?\n"
            "A: Installment 1 (April-July), Installment 2 (August-November), Installment 3 (December-March). Each installment is Rs 2,000.\n\n"
            "Q: My PM-Kisan payment is stuck. What should I do?\n"
            "A: Common reasons: (1) Aadhaar not linked to bank - visit bank to link, (2) Aadhaar mismatch - contact agriculture officer, (3) Land records not verified - contact Patwari, (4) Wrong bank details - update at pmkisan.gov.in. Call 155261 for help.\n\n"
            "Q: Can tenant farmers or sharecroppers get PM-Kisan?\n"
            "A: No. Only farmers who own land in their name are eligible. Tenant farmers and sharecroppers are not covered.\n\n"
            "Q: Who is NOT eligible for PM-Kisan?\n"
            "A: Income tax payers, government employees (except Class 4), pensioners with Rs 10,000+ monthly pension, professionals (doctors, engineers, lawyers, CAs), and institutional landholders.\n\n"
            "Q: Can more than one family member get PM-Kisan?\n"
            "A: No. Only one person per family can get PM-Kisan. Family means husband, wife, and minor children.\n\n"
            "Q: How to do eKYC for PM-Kisan?\n"
            "A: Go to pmkisan.gov.in > eKYC option > enter Aadhaar number > verify with OTP sent to Aadhaar-linked mobile. eKYC is mandatory for receiving installments.\n\n"
            "Q: Is PM-Kisan available in all states?\n"
            "A: Yes, in all states and union territories. West Bengal runs its own scheme (Krishak Bandhu) instead."
        ),
        "text_hi": (
            "पीएम किसान सम्मान निधि के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: पीएम किसान में कितने पैसे मिलते हैं?\n"
            "उत्तर: हर साल 6,000 रुपये मिलते हैं, जो 2,000-2,000 रुपये की 3 किस्तों में सीधे आधार से जुड़े बैंक खाते में आते हैं। हर 4 महीने में एक किस्त।\n\n"
            "प्रश्न: पीएम किसान के लिए कौन से दस्तावेज चाहिए?\n"
            "उत्तर: आधार कार्ड, आधार से लिंक बैंक खाता पासबुक, जमीन के कागजात (खतौनी/खसरा), और मोबाइल नंबर। आधार-बैंक लिंकिंग अनिवार्य है।\n\n"
            "प्रश्न: पीएम किसान का पेमेंट स्टेटस कैसे चेक करें?\n"
            "उत्तर: pmkisan.gov.in पर 'Beneficiary Status' पर क्लिक करें। आधार नंबर, मोबाइल नंबर या खाता नंबर से चेक करें। हेल्पलाइन 155261 या 011-24300606 पर भी कॉल करें।\n\n"
            "प्रश्न: पीएम किसान की किस्तें कब आती हैं?\n"
            "उत्तर: किस्त 1 (अप्रैल-जुलाई), किस्त 2 (अगस्त-नवंबर), किस्त 3 (दिसंबर-मार्च)। हर किस्त 2,000 रुपये।\n\n"
            "प्रश्न: मेरा पीएम किसान का पैसा रुका है, क्या करूं?\n"
            "उत्तर: सामान्य कारण: (1) आधार बैंक से लिंक नहीं - बैंक जाकर लिंक कराएं, (2) आधार नंबर गलत - कृषि अधिकारी से मिलें, (3) जमीन रिकॉर्ड सत्यापित नहीं - पटवारी से मिलें, (4) बैंक जानकारी गलत - pmkisan.gov.in पर अपडेट करें। 155261 पर कॉल करें।\n\n"
            "प्रश्न: क्या बटाईदार किसान को पीएम किसान मिलेगा?\n"
            "उत्तर: नहीं। केवल जिनके नाम पर जमीन है वे पात्र हैं।\n\n"
            "प्रश्न: कौन पात्र नहीं है?\n"
            "उत्तर: आयकरदाता, सरकारी कर्मचारी (श्रेणी 4 छोड़कर), 10,000+ मासिक पेंशनभोगी, पेशेवर (डॉक्टर, इंजीनियर, वकील, सीए), संस्थागत भूमिधारक।\n\n"
            "प्रश्न: एक परिवार में कितने लोगों को मिलेगा?\n"
            "उत्तर: एक परिवार में केवल एक व्यक्ति को। परिवार यानी पति, पत्नी और नाबालिग बच्चे।\n\n"
            "प्रश्न: eKYC कैसे करें?\n"
            "उत्तर: pmkisan.gov.in > eKYC > आधार नंबर डालें > आधार-लिंक मोबाइल पर OTP से सत्यापित करें। किस्त पाने के लिए eKYC अनिवार्य है।"
        ),
    },
    # ── Ayushman Bharat FAQs ──────────────────────────────────────────────
    {
        "scheme_id": "ayushman-bharat",
        "section_id": "faqs",
        "category": "health",
        "name_en": "Ayushman Bharat FAQs",
        "name_hi": "आयुष्मान भारत अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Ayushman Bharat (PM-JAY):\n\n"
            "Q: How much health insurance do I get under Ayushman Bharat?\n"
            "A: Rs 5 lakh per family per year for secondary and tertiary hospitalization. This covers the entire family, not per person.\n\n"
            "Q: How to check if I am eligible for Ayushman Bharat?\n"
            "A: Visit mera.pmjay.gov.in, enter your mobile number, and verify with OTP. Or call 14555. Or visit any Ayushman Mitra at empanelled hospitals.\n\n"
            "Q: Which hospitals accept Ayushman Bharat card?\n"
            "A: All government hospitals and empanelled private hospitals. Find the nearest one at pmjay.gov.in > Hospital Finder or call 14555.\n\n"
            "Q: What diseases and treatments are covered?\n"
            "A: Over 1,929 medical packages including surgery, medical treatment, day care, ICU, diagnostics, medicines, and follow-up care. Pre-existing diseases are also covered from day one.\n\n"
            "Q: How to get an Ayushman card?\n"
            "A: Visit any empanelled hospital, CSC centre, or Ayushman Arogya Mandir with Aadhaar card. Your eligibility will be verified and e-card generated on the spot. Card is free.\n\n"
            "Q: Is there any age limit for Ayushman Bharat?\n"
            "A: No age limit. All family members are covered regardless of age, gender, or family size.\n\n"
            "Q: Can I use Ayushman Bharat in another state?\n"
            "A: Yes. Ayushman Bharat is portable across India. You can get treatment at any empanelled hospital in any state.\n\n"
            "Q: What if the hospital refuses Ayushman treatment?\n"
            "A: Call the Ayushman helpline 14555 to file a complaint. Empanelled hospitals cannot refuse treatment to eligible beneficiaries.\n\n"
            "Q: Do I need to pay anything at the hospital?\n"
            "A: No. Treatment is completely cashless and paperless. The hospital settles claims directly with the insurance company. You pay nothing.\n\n"
            "Q: What is NOT covered under Ayushman Bharat?\n"
            "A: OPD (outpatient) consultations, cosmetic surgery, fertility treatment, organ transplant, and drug rehabilitation are generally not covered."
        ),
        "text_hi": (
            "आयुष्मान भारत (PM-JAY) के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: आयुष्मान भारत में कितना स्वास्थ्य बीमा मिलता है?\n"
            "उत्तर: प्रति परिवार प्रति वर्ष 5 लाख रुपये तक का बीमा। यह पूरे परिवार के लिए है, प्रति व्यक्ति नहीं।\n\n"
            "प्रश्न: मैं आयुष्मान भारत के लिए पात्र हूं या नहीं, कैसे जानें?\n"
            "उत्तर: mera.pmjay.gov.in पर जाएं, मोबाइल नंबर डालें और OTP से सत्यापित करें। या 14555 पर कॉल करें। या किसी सूचीबद्ध अस्पताल में आयुष्मान मित्र से मिलें।\n\n"
            "प्रश्न: कौन से अस्पताल आयुष्मान कार्ड स्वीकार करते हैं?\n"
            "उत्तर: सभी सरकारी अस्पताल और सूचीबद्ध निजी अस्पताल। pmjay.gov.in > Hospital Finder पर या 14555 पर कॉल करके पता करें।\n\n"
            "प्रश्न: कौन सी बीमारियां और इलाज कवर होते हैं?\n"
            "उत्तर: 1,929 से अधिक चिकित्सा पैकेज - सर्जरी, इलाज, डे केयर, ICU, जांच, दवाइयां और फॉलो-अप। पहले से मौजूद बीमारियां भी पहले दिन से कवर।\n\n"
            "प्रश्न: आयुष्मान कार्ड कैसे बनवाएं?\n"
            "उत्तर: किसी सूचीबद्ध अस्पताल, CSC केंद्र या आयुष्मान आरोग्य मंदिर में आधार लेकर जाएं। पात्रता सत्यापित होगी और ई-कार्ड मौके पर बनेगा। कार्ड मुफ्त है।\n\n"
            "प्रश्न: क्या आयुष्मान भारत में उम्र की सीमा है?\n"
            "उत्तर: नहीं। परिवार के सभी सदस्य उम्र, लिंग या परिवार के आकार की परवाह किए बिना कवर हैं।\n\n"
            "प्रश्न: क्या दूसरे राज्य में इलाज करा सकते हैं?\n"
            "उत्तर: हां। आयुष्मान भारत पूरे भारत में पोर्टेबल है। किसी भी राज्य के सूचीबद्ध अस्पताल में इलाज करा सकते हैं।\n\n"
            "प्रश्न: अगर अस्पताल इलाज से मना करे तो?\n"
            "उत्तर: 14555 पर कॉल करके शिकायत करें। सूचीबद्ध अस्पताल पात्र लाभार्थियों को इलाज से मना नहीं कर सकते।\n\n"
            "प्रश्न: क्या अस्पताल में कुछ पैसे देने होंगे?\n"
            "उत्तर: नहीं। इलाज पूरी तरह कैशलेस और पेपरलेस है। अस्पताल सीधे बीमा कंपनी से दावा करता है।"
        ),
    },
    # ── MGNREGA FAQs ──────────────────────────────────────────────────────
    {
        "scheme_id": "mgnrega",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "MGNREGA FAQs",
        "name_hi": "मनरेगा अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about MGNREGA:\n\n"
            "Q: How many days of work does MGNREGA give?\n"
            "A: 100 days of guaranteed paid work per financial year per rural household.\n\n"
            "Q: What is the daily wage under MGNREGA?\n"
            "A: Rs 200 to Rs 350 per day depending on your state. Wages are revised annually. Check nrega.nic.in for your state's rate.\n\n"
            "Q: How to get a MGNREGA job card?\n"
            "A: Apply at your gram panchayat office with Aadhaar, photos, and bank details. Job card is issued within 15 days. It is free.\n\n"
            "Q: How to demand work under MGNREGA?\n"
            "A: Submit a written application at your gram panchayat asking for work. You must get work within 15 days. Keep the receipt of your application.\n\n"
            "Q: What if I don't get work within 15 days?\n"
            "A: You are entitled to unemployment allowance - one-fourth of the wage rate for first 30 days and one-half thereafter. File a complaint at nrega.nic.in.\n\n"
            "Q: How to check MGNREGA payment status?\n"
            "A: Visit nrega.nic.in > select your state, district, block, and panchayat > check job card details and payment status. Payments go directly to bank/post office account.\n\n"
            "Q: Can women work under MGNREGA?\n"
            "A: Yes. At least one-third of all MGNREGA work days are reserved for women. Equal wages for men and women.\n\n"
            "Q: What kind of work is done under MGNREGA?\n"
            "A: Water conservation, drought proofing, land development, rural roads, flood control, irrigation channels, renovation of traditional water bodies, and individual land development for SC/ST/BPL families.\n\n"
            "Q: When is MGNREGA payment made?\n"
            "A: Wages must be paid within 15 days of completing work. Payment goes directly to bank account. Delayed payment attracts compensation.\n\n"
            "Q: Where to complain about MGNREGA issues?\n"
            "A: File complaint at nrega.nic.in > Grievance section, or call 1800-111-555, or write to the District Programme Coordinator."
        ),
        "text_hi": (
            "मनरेगा के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: मनरेगा में कितने दिन काम मिलता है?\n"
            "उत्तर: प्रति ग्रामीण परिवार को प्रति वित्तीय वर्ष में 100 दिन गारंटीशुदा काम।\n\n"
            "प्रश्न: मनरेगा में रोज कितनी मजदूरी मिलती है?\n"
            "उत्तर: राज्य के अनुसार 200 से 350 रुपये प्रतिदिन। हर साल संशोधित होती है। nrega.nic.in पर अपने राज्य की दर देखें।\n\n"
            "प्रश्न: मनरेगा जॉब कार्ड कैसे बनवाएं?\n"
            "उत्तर: ग्राम पंचायत में आधार, फोटो और बैंक जानकारी लेकर आवेदन करें। 15 दिन में जॉब कार्ड मिल जाएगा। यह मुफ्त है।\n\n"
            "प्रश्न: मनरेगा में काम कैसे मांगें?\n"
            "उत्तर: ग्राम पंचायत में लिखित आवेदन दें। 15 दिन में काम मिलना चाहिए। आवेदन की रसीद रखें।\n\n"
            "प्रश्न: 15 दिन में काम न मिले तो?\n"
            "उत्तर: बेरोजगारी भत्ता मिलेगा - पहले 30 दिन मजदूरी का एक-चौथाई, उसके बाद आधा। nrega.nic.in पर शिकायत दर्ज करें।\n\n"
            "प्रश्न: मनरेगा पेमेंट स्टेटस कैसे देखें?\n"
            "उत्तर: nrega.nic.in > अपना राज्य, जिला, ब्लॉक, पंचायत चुनें > जॉब कार्ड और भुगतान विवरण देखें।\n\n"
            "प्रश्न: क्या महिलाएं मनरेगा में काम कर सकती हैं?\n"
            "उत्तर: हां। कम से कम एक-तिहाई कार्य दिवस महिलाओं के लिए आरक्षित हैं। पुरुषों और महिलाओं को समान मजदूरी।\n\n"
            "प्रश्न: मनरेगा में कौन सा काम होता है?\n"
            "उत्तर: जल संरक्षण, सूखा रोकथाम, भूमि विकास, ग्रामीण सड़कें, बाढ़ नियंत्रण, सिंचाई नहर, पारंपरिक जल निकायों का नवीनीकरण।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: nrega.nic.in > शिकायत खंड, या 1800-111-555 पर कॉल करें, या जिला कार्यक्रम समन्वयक को लिखें।"
        ),
    },
    # ── PM Awas Yojana FAQs ───────────────────────────────────────────────
    {
        "scheme_id": "pm-awas-yojana",
        "section_id": "faqs",
        "category": "housing",
        "name_en": "PM Awas Yojana FAQs",
        "name_hi": "पीएम आवास योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Awas Yojana:\n\n"
            "Q: How much money do I get under PM Awas Yojana?\n"
            "A: Rural (PMAY-G): Rs 1.20 lakh in plains, Rs 1.30 lakh in hilly areas. Urban (PMAY-U): Interest subsidy of 3-6.5% on home loan depending on income category - EWS/LIG get Rs 2.67 lakh subsidy, MIG-I get Rs 2.35 lakh, MIG-II get Rs 2.30 lakh.\n\n"
            "Q: Who is eligible for PM Awas Yojana?\n"
            "A: Families without a pucca house anywhere in India. EWS (annual income up to Rs 3 lakh), LIG (Rs 3-6 lakh), MIG-I (Rs 6-12 lakh), MIG-II (Rs 12-18 lakh).\n\n"
            "Q: How to apply for PM Awas Yojana?\n"
            "A: Rural: Apply at gram panchayat. Urban: Apply online at pmaymis.gov.in or at nearest CSC or Urban Local Body office. Carry Aadhaar, income certificate, and bank details.\n\n"
            "Q: How to check PM Awas Yojana application status?\n"
            "A: Rural: Visit pmayg.nic.in and search by name or registration number. Urban: Visit pmaymis.gov.in > Track Your Assessment Status > enter Aadhaar or assessment ID.\n\n"
            "Q: How long does it take to get PM Awas Yojana money?\n"
            "A: Rural: 6-12 months for selection and first installment. Money comes in 3-4 installments based on construction progress. Urban: Loan subsidy credited within 3-4 months of loan disbursement.\n\n"
            "Q: Can I apply if I already have a house?\n"
            "A: No. If you or any family member owns a pucca house anywhere in India, you are not eligible.\n\n"
            "Q: What if my PMAY application is rejected?\n"
            "A: Common reasons: already own pucca house, income above limit, incomplete documents. Re-apply with correct documents or file grievance at pmayg.nic.in or pmaymis.gov.in.\n\n"
            "Q: Where to complain about PM Awas Yojana?\n"
            "A: Call 1800-11-6163 (toll-free). Or file a grievance on the PMAY portal. Or contact District Collector/Municipal Commissioner."
        ),
        "text_hi": (
            "पीएम आवास योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: पीएम आवास योजना में कितने पैसे मिलते हैं?\n"
            "उत्तर: ग्रामीण (PMAY-G): मैदानी क्षेत्र में 1.20 लाख, पहाड़ी क्षेत्र में 1.30 लाख। शहरी (PMAY-U): होम लोन पर 3-6.5% ब्याज सब्सिडी - EWS/LIG को 2.67 लाख, MIG-I को 2.35 लाख, MIG-II को 2.30 लाख सब्सिडी।\n\n"
            "प्रश्न: पीएम आवास योजना के लिए कौन पात्र है?\n"
            "उत्तर: जिनके पास भारत में कहीं भी पक्का मकान नहीं हो। EWS (वार्षिक आय 3 लाख तक), LIG (3-6 लाख), MIG-I (6-12 लाख), MIG-II (12-18 लाख)।\n\n"
            "प्रश्न: आवेदन कैसे करें?\n"
            "उत्तर: ग्रामीण: ग्राम पंचायत में आवेदन करें। शहरी: pmaymis.gov.in पर ऑनलाइन या CSC/शहरी स्थानीय निकाय में। आधार, आय प्रमाण पत्र और बैंक जानकारी लें।\n\n"
            "प्रश्न: आवेदन की स्थिति कैसे जांचें?\n"
            "उत्तर: ग्रामीण: pmayg.nic.in पर नाम या पंजीकरण संख्या से खोजें। शहरी: pmaymis.gov.in > Track Your Assessment Status > आधार या असेसमेंट ID डालें।\n\n"
            "प्रश्न: पैसा कब तक आता है?\n"
            "उत्तर: ग्रामीण: चयन और पहली किस्त में 6-12 महीने। निर्माण प्रगति के आधार पर 3-4 किस्तों में पैसा आता है। शहरी: लोन वितरण के 3-4 महीने में सब्सिडी।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: 1800-11-6163 (टोल-फ्री) पर कॉल करें। PMAY पोर्टल पर शिकायत दर्ज करें। या जिला कलेक्टर/नगर आयुक्त से संपर्क करें।"
        ),
    },
    # ── Sukanya Samriddhi FAQs ────────────────────────────────────────────
    {
        "scheme_id": "sukanya-samriddhi",
        "section_id": "faqs",
        "category": "women",
        "name_en": "Sukanya Samriddhi Yojana FAQs",
        "name_hi": "सुकन्या समृद्धि योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Sukanya Samriddhi Yojana:\n\n"
            "Q: What is the current interest rate of Sukanya Samriddhi?\n"
            "A: The interest rate is set by the government quarterly. It is typically around 8-8.2% per annum, one of the highest among small savings schemes.\n\n"
            "Q: What is the minimum and maximum deposit?\n"
            "A: Minimum Rs 250 per year, maximum Rs 1.5 lakh per year. Deposits must be made for the first 15 years after opening.\n\n"
            "Q: When does the Sukanya Samriddhi account mature?\n"
            "A: The account matures 21 years after opening, or when the girl gets married after age 18 (whichever is earlier). Partial withdrawal (up to 50%) allowed after the girl turns 18 for education.\n\n"
            "Q: What are the tax benefits?\n"
            "A: Triple tax benefit under Section 80C: deposits up to Rs 1.5 lakh are tax-deductible, interest earned is tax-free, and maturity amount is tax-free.\n\n"
            "Q: How many accounts can be opened per family?\n"
            "A: Maximum 2 accounts per family (one per girl child). For twin girls, a third account can be opened with proof.\n\n"
            "Q: Can the account be transferred to another bank or post office?\n"
            "A: Yes. The account can be transferred anywhere in India from one post office/bank to another.\n\n"
            "Q: What happens if I miss depositing in a year?\n"
            "A: The account becomes inactive. To reactivate, pay Rs 50 penalty per year of default plus the minimum annual deposit of Rs 250.\n\n"
            "Q: Can I close the account early?\n"
            "A: Premature closure is allowed after 5 years in case of the account holder's death, life-threatening illness, or guardian's death. Otherwise, account runs till maturity."
        ),
        "text_hi": (
            "सुकन्या समृद्धि योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: सुकन्या समृद्धि की वर्तमान ब्याज दर क्या है?\n"
            "उत्तर: ब्याज दर सरकार हर तिमाही तय करती है। आमतौर पर 8-8.2% सालाना, छोटी बचत योजनाओं में सबसे अधिक।\n\n"
            "प्रश्न: न्यूनतम और अधिकतम जमा कितनी है?\n"
            "उत्तर: न्यूनतम 250 रुपये सालाना, अधिकतम 1.5 लाख सालाना। खाता खुलने के पहले 15 साल तक जमा करना होता है।\n\n"
            "प्रश्न: खाता कब परिपक्व होता है?\n"
            "उत्तर: खाता खोलने के 21 साल बाद या बेटी की 18 साल बाद शादी (जो पहले हो)। 18 साल बाद शिक्षा के लिए 50% निकासी संभव।\n\n"
            "प्रश्न: टैक्स में क्या फायदा है?\n"
            "उत्तर: धारा 80C के तहत तिहरा लाभ: 1.5 लाख तक जमा पर कर छूट, ब्याज कर-मुक्त, और परिपक्वता राशि कर-मुक्त।\n\n"
            "प्रश्न: एक परिवार में कितने खाते खुल सकते हैं?\n"
            "उत्तर: अधिकतम 2 (एक बेटी का एक)। जुड़वां बेटियों के लिए प्रमाण देकर तीसरा खाता खुल सकता है।\n\n"
            "प्रश्न: साल में जमा न कर पाएं तो?\n"
            "उत्तर: खाता निष्क्रिय हो जाएगा। सक्रिय करने के लिए 50 रुपये प्रति वर्ष जुर्माना और 250 रुपये न्यूनतम जमा देना होगा।"
        ),
    },
    # ── PM Mudra Yojana FAQs ──────────────────────────────────────────────
    {
        "scheme_id": "pm-mudra-yojana",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM Mudra Yojana FAQs",
        "name_hi": "पीएम मुद्रा योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Mudra Yojana (PMMY):\n\n"
            "Q: What are the different types of Mudra loans?\n"
            "A: Four categories: Shishu (up to Rs 50,000), Kishore (Rs 50,001 to Rs 5 lakh), Tarun (Rs 5 lakh to Rs 10 lakh), and Tarun Plus (Rs 10 lakh to Rs 20 lakh).\n\n"
            "Q: What is the interest rate on Mudra loans?\n"
            "A: Interest rates vary by bank but are generally between 7-12% per annum. No fixed rate - banks decide based on risk assessment.\n\n"
            "Q: Is collateral or guarantee required?\n"
            "A: No collateral needed for loans up to Rs 10 lakh. For Tarun Plus (above Rs 10 lakh), banks may ask for collateral.\n\n"
            "Q: What businesses qualify for Mudra loans?\n"
            "A: Any non-farm small business: shops, vendors, tailors, repair shops, salons, food stalls, small manufacturers, transport operators, artisans etc.\n\n"
            "Q: How long to repay a Mudra loan?\n"
            "A: Repayment period is up to 5 years for term loans. Working capital loans are renewed annually.\n\n"
            "Q: Where to apply for a Mudra loan?\n"
            "A: Any commercial bank, Regional Rural Bank, Small Finance Bank, NBFC, or MFI. Also online at udyamimitra.in or mudra.org.in.\n\n"
            "Q: My Mudra loan application was rejected. What to do?\n"
            "A: Common reasons: poor credit score, no business plan, incomplete documents. Improve your application and try another bank. You can also apply through NBFC or MFI.\n\n"
            "Q: Can I get a Mudra loan for agriculture?\n"
            "A: No. Mudra loans are only for non-farm businesses. For agriculture loans, apply under Kisan Credit Card or other farm loan schemes."
        ),
        "text_hi": (
            "पीएम मुद्रा योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: मुद्रा लोन कितने प्रकार के हैं?\n"
            "उत्तर: चार श्रेणियां: शिशु (50,000 तक), किशोर (50,001 से 5 लाख), तरुण (5 से 10 लाख), तरुण प्लस (10 से 20 लाख)।\n\n"
            "प्रश्न: मुद्रा लोन पर ब्याज दर क्या है?\n"
            "उत्तर: ब्याज दर बैंक अनुसार 7-12% सालाना। कोई निश्चित दर नहीं - बैंक जोखिम के आधार पर तय करता है।\n\n"
            "प्रश्न: क्या गारंटी या जमानत चाहिए?\n"
            "उत्तर: 10 लाख तक के लोन में कोई गारंटी नहीं। तरुण प्लस (10 लाख से ऊपर) में बैंक गारंटी मांग सकता है।\n\n"
            "प्रश्न: कौन से बिजनेस के लिए मुद्रा लोन मिलता है?\n"
            "उत्तर: कोई भी गैर-कृषि छोटा व्यवसाय: दुकान, फेरीवाला, दर्जी, मरम्मत, सैलून, खाद्य स्टॉल, छोटा निर्माण, परिवहन, कारीगर आदि।\n\n"
            "प्रश्न: मुद्रा लोन कहां से लें?\n"
            "उत्तर: किसी भी व्यावसायिक बैंक, ग्रामीण बैंक, स्मॉल फाइनेंस बैंक, NBFC या MFI से। udyamimitra.in या mudra.org.in पर ऑनलाइन भी।\n\n"
            "प्रश्न: क्या कृषि के लिए मुद्रा लोन मिलेगा?\n"
            "उत्तर: नहीं। मुद्रा लोन सिर्फ गैर-कृषि व्यवसाय के लिए है। कृषि ऋण के लिए किसान क्रेडिट कार्ड या अन्य कृषि ऋण योजना में आवेदन करें।"
        ),
    },
    # ── PM Fasal Bima FAQs ────────────────────────────────────────────────
    {
        "scheme_id": "pm-fasal-bima",
        "section_id": "faqs",
        "category": "agriculture",
        "name_en": "PM Fasal Bima Yojana FAQs",
        "name_hi": "पीएम फसल बीमा योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Fasal Bima Yojana:\n\n"
            "Q: How much premium do farmers pay?\n"
            "A: Kharif crops: 2% of sum insured. Rabi crops: 1.5%. Commercial/horticultural crops: 5%. Government pays the remaining premium.\n\n"
            "Q: What crop losses are covered?\n"
            "A: Natural calamities (flood, drought, hail, cyclone, pest attack), prevented sowing, mid-season adversity, post-harvest losses (up to 14 days), and localized calamities.\n\n"
            "Q: How to file a crop insurance claim?\n"
            "A: Report crop loss within 72 hours to the insurance company, bank, agriculture office, or via the Crop Insurance App. Call 14447 for guidance.\n\n"
            "Q: How long does claim settlement take?\n"
            "A: Claims should be settled within 2 months of harvest. If delayed, insurance company pays 12% interest on the delayed amount.\n\n"
            "Q: Is PM Fasal Bima mandatory?\n"
            "A: Voluntary for all farmers since Kharif 2020. Even loanee farmers can opt out by informing their bank before the cut-off date.\n\n"
            "Q: When is the last date to apply?\n"
            "A: Cut-off dates are fixed each season. Typically: Kharif: July 31, Rabi: December 31. Check pmfby.gov.in for exact dates.\n\n"
            "Q: How to check PM Fasal Bima claim status?\n"
            "A: Visit pmfby.gov.in > Application Status, or use the Crop Insurance App, or call 14447.\n\n"
            "Q: Can tenant farmers get crop insurance?\n"
            "A: Yes. Tenant and sharecropper farmers can also enroll with appropriate land documents."
        ),
        "text_hi": (
            "पीएम फसल बीमा योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: किसान को कितना प्रीमियम देना होता है?\n"
            "उत्तर: खरीफ: बीमित राशि का 2%। रबी: 1.5%। व्यावसायिक/बागवानी फसल: 5%। बाकी प्रीमियम सरकार देती है।\n\n"
            "प्रश्न: कौन सी फसल हानि कवर होती है?\n"
            "उत्तर: प्राकृतिक आपदा (बाढ़, सूखा, ओलावृष्टि, चक्रवात, कीट), बुआई रोकी गई, मध्य-मौसम प्रतिकूलता, कटाई बाद नुकसान (14 दिन तक), स्थानीय आपदा।\n\n"
            "प्रश्न: फसल बीमा दावा कैसे करें?\n"
            "उत्तर: फसल नुकसान के 72 घंटे के भीतर बीमा कंपनी, बैंक, कृषि कार्यालय या Crop Insurance App पर सूचित करें। 14447 पर कॉल करें।\n\n"
            "प्रश्न: दावा कितने दिन में मिलता है?\n"
            "उत्तर: कटाई के 2 महीने में दावा निपटान होना चाहिए। देरी पर बीमा कंपनी 12% ब्याज देती है।\n\n"
            "प्रश्न: क्या फसल बीमा अनिवार्य है?\n"
            "उत्तर: खरीफ 2020 से सभी किसानों के लिए स्वैच्छिक। कर्ज लेने वाले किसान भी अंतिम तिथि से पहले बैंक को सूचित करके बाहर हो सकते हैं।\n\n"
            "प्रश्न: दावे की स्थिति कैसे जांचें?\n"
            "उत्तर: pmfby.gov.in > Application Status, या Crop Insurance App, या 14447 पर कॉल करें।"
        ),
    },
    # ── Atal Pension Yojana FAQs ──────────────────────────────────────────
    {
        "scheme_id": "atal-pension-yojana",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "Atal Pension Yojana FAQs",
        "name_hi": "अटल पेंशन योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Atal Pension Yojana (APY):\n\n"
            "Q: How much pension will I get?\n"
            "A: You choose: Rs 1,000, Rs 2,000, Rs 3,000, Rs 4,000, or Rs 5,000 per month after age 60. Higher pension = higher monthly contribution.\n\n"
            "Q: How much do I need to contribute per month?\n"
            "A: Depends on your age and chosen pension. Example: For Rs 5,000 pension, if you join at age 18 you pay Rs 210/month, at age 30 you pay Rs 577/month, at age 40 you pay Rs 1,454/month.\n\n"
            "Q: What happens after I die?\n"
            "A: Your spouse gets the same pension for life. After spouse's death, the accumulated corpus is returned to the nominee.\n\n"
            "Q: Can I exit APY before 60?\n"
            "A: Voluntary exit before 60 returns only your contribution plus interest earned (not government's co-contribution). Exit allowed only in exceptional circumstances.\n\n"
            "Q: Can income tax payers join APY?\n"
            "A: No. From October 1, 2022, income tax payers are not eligible to join APY.\n\n"
            "Q: How to check APY account balance?\n"
            "A: Through your bank's net banking/mobile banking, or visit enps.nsdl.com, or ask at your bank branch.\n\n"
            "Q: Can I change my pension amount later?\n"
            "A: Yes. You can increase or decrease your pension amount once per year during April. Visit your bank to request the change.\n\n"
            "Q: What if I miss a monthly contribution?\n"
            "A: A penalty of Rs 1-10 per month is charged. If overdue for 6 months, the account is frozen. After 12 months, it is closed."
        ),
        "text_hi": (
            "अटल पेंशन योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: कितनी पेंशन मिलेगी?\n"
            "उत्तर: आप चुनें: 60 साल बाद 1,000, 2,000, 3,000, 4,000 या 5,000 रुपये मासिक। ज्यादा पेंशन = ज्यादा मासिक योगदान।\n\n"
            "प्रश्न: हर महीने कितना देना होगा?\n"
            "उत्तर: उम्र और चुनी गई पेंशन पर निर्भर। उदाहरण: 5,000 रुपये पेंशन के लिए - 18 साल में जुड़ें तो 210/माह, 30 साल में 577/माह, 40 साल में 1,454/माह।\n\n"
            "प्रश्न: मेरी मृत्यु के बाद क्या होगा?\n"
            "उत्तर: पति/पत्नी को जीवन भर वही पेंशन मिलेगी। उनकी मृत्यु के बाद जमा राशि नॉमिनी को वापस।\n\n"
            "प्रश्न: क्या आयकरदाता APY में शामिल हो सकते हैं?\n"
            "उत्तर: नहीं। 1 अक्टूबर 2022 से आयकरदाता APY में शामिल नहीं हो सकते।\n\n"
            "प्रश्न: APY बैलेंस कैसे चेक करें?\n"
            "उत्तर: बैंक की नेट बैंकिंग/मोबाइल बैंकिंग से, या enps.nsdl.com पर, या बैंक शाखा में पूछें।\n\n"
            "प्रश्न: पेंशन राशि बाद में बदल सकते हैं?\n"
            "उत्तर: हां। अप्रैल में साल में एक बार बढ़ा या घटा सकते हैं। बैंक में जाकर अनुरोध करें।\n\n"
            "प्रश्न: मासिक योगदान छूट जाए तो?\n"
            "उत्तर: 1-10 रुपये प्रति माह जुर्माना। 6 महीने बकाया पर खाता फ्रीज। 12 महीने बाद बंद।"
        ),
    },
    # ── PM SVANidhi FAQs ──────────────────────────────────────────────────
    {
        "scheme_id": "pm-svanidhi",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM SVANidhi FAQs",
        "name_hi": "पीएम स्वनिधि अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM SVANidhi:\n\n"
            "Q: How much loan can I get under PM SVANidhi?\n"
            "A: First loan: Rs 10,000. Second loan: Rs 20,000 (after repaying first). Third loan: Rs 50,000 (after repaying second).\n\n"
            "Q: What is the interest rate?\n"
            "A: Banks charge regular interest but the government gives 7% interest subsidy per annum. So your effective interest is lower.\n\n"
            "Q: Do I need any guarantee or collateral?\n"
            "A: No. PM SVANidhi loans are collateral-free and guarantee-free.\n\n"
            "Q: How long do I have to repay?\n"
            "A: Each loan must be repaid in 12 monthly installments. Timely repayment qualifies you for the next higher loan.\n\n"
            "Q: What is the cashback benefit?\n"
            "A: Street vendors who use digital payment methods (UPI, QR code) get cashback of up to Rs 1,200 per year.\n\n"
            "Q: Who is eligible for PM SVANidhi?\n"
            "A: Street vendors who were vending on or before March 24, 2020, with a Certificate of Vending or Letter of Recommendation from the Urban Local Body.\n\n"
            "Q: How to apply for PM SVANidhi?\n"
            "A: Apply online at pmsvanidhi.mohua.gov.in or through the PM SVANidhi app. CSC centres also help with applications.\n\n"
            "Q: How to check PM SVANidhi loan status?\n"
            "A: Log in at pmsvanidhi.mohua.gov.in with your mobile number, or call 1800-11-1979."
        ),
        "text_hi": (
            "पीएम स्वनिधि के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: पीएम स्वनिधि में कितना लोन मिलता है?\n"
            "उत्तर: पहला लोन: 10,000 रुपये। दूसरा: 20,000 (पहला चुकाने के बाद)। तीसरा: 50,000 (दूसरा चुकाने के बाद)।\n\n"
            "प्रश्न: ब्याज दर क्या है?\n"
            "उत्तर: बैंक नियमित ब्याज लेता है लेकिन सरकार 7% सालाना ब्याज सब्सिडी देती है।\n\n"
            "प्रश्न: गारंटी या जमानत चाहिए?\n"
            "उत्तर: नहीं। स्वनिधि लोन बिना गारंटी और बिना जमानत मिलता है।\n\n"
            "प्रश्न: लोन कितने समय में चुकाना होता है?\n"
            "उत्तर: हर लोन 12 मासिक किस्तों में चुकाना होता है। समय पर चुकाने पर अगला बड़ा लोन मिलता है।\n\n"
            "प्रश्न: कैशबैक क्या है?\n"
            "उत्तर: डिजिटल भुगतान (UPI, QR कोड) इस्तेमाल करने वाले विक्रेताओं को सालाना 1,200 रुपये तक कैशबैक।\n\n"
            "प्रश्न: आवेदन कैसे करें?\n"
            "उत्तर: pmsvanidhi.mohua.gov.in पर ऑनलाइन या PM स्वनिधि ऐप से। CSC केंद्र भी मदद करते हैं।\n\n"
            "प्रश्न: लोन की स्थिति कैसे जांचें?\n"
            "उत्तर: pmsvanidhi.mohua.gov.in पर मोबाइल नंबर से लॉगिन करें, या 1800-11-1979 पर कॉल करें।"
        ),
    },
    # ── Beti Bachao Beti Padhao FAQs ──────────────────────────────────────
    {
        "scheme_id": "beti-bachao-beti-padhao",
        "section_id": "faqs",
        "category": "women",
        "name_en": "Beti Bachao Beti Padhao FAQs",
        "name_hi": "बेटी बचाओ बेटी पढ़ाओ अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Beti Bachao Beti Padhao:\n\n"
            "Q: Is Beti Bachao Beti Padhao a financial scheme?\n"
            "A: No, it is mainly an awareness campaign. It does not give direct cash. But it connects to other schemes like Sukanya Samriddhi, scholarships, and CBSE Udaan for girls.\n\n"
            "Q: What are the objectives of the scheme?\n"
            "A: (1) Prevent gender-biased sex selection and female foeticide, (2) Ensure survival and protection of girl children, (3) Ensure education and participation of girls.\n\n"
            "Q: How does it benefit my daughter?\n"
            "A: Through improved health services for girls, better school enrollment campaigns, awareness against child marriage, and connecting families to financial schemes for girls.\n\n"
            "Q: Is there a helpline for girls' safety?\n"
            "A: Yes. Women Helpline: 181 (for any issue related to women/girls). Child Helpline: 1098 (for child protection issues).\n\n"
            "Q: How can I report female foeticide or sex determination?\n"
            "A: Call 181 or contact your District Magistrate office. Pre-natal sex determination is illegal under the PCPNDT Act 1994. Report anonymously.\n\n"
            "Q: What related financial schemes are available for girls?\n"
            "A: Sukanya Samriddhi Yojana (savings), National Scholarship Portal (education), Ladli Laxmi (state schemes), state-specific girl child schemes."
        ),
        "text_hi": (
            "बेटी बचाओ बेटी पढ़ाओ के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: क्या यह कोई वित्तीय योजना है?\n"
            "उत्तर: नहीं, यह मुख्य रूप से जागरूकता अभियान है। सीधे पैसे नहीं मिलते। लेकिन सुकन्या समृद्धि, छात्रवृत्ति और CBSE उड़ान जैसी योजनाओं से जोड़ती है।\n\n"
            "प्रश्न: इस योजना के उद्देश्य क्या हैं?\n"
            "उत्तर: (1) लिंग आधारित चयन और कन्या भ्रूण हत्या रोकना, (2) बालिकाओं की सुरक्षा सुनिश्चित करना, (3) लड़कियों की शिक्षा और भागीदारी सुनिश्चित करना।\n\n"
            "प्रश्न: मेरी बेटी को क्या फायदा होगा?\n"
            "उत्तर: बेहतर स्वास्थ्य सेवाएं, स्कूल नामांकन अभियान, बाल विवाह विरोधी जागरूकता, और बेटियों के लिए वित्तीय योजनाओं से जोड़ना।\n\n"
            "प्रश्न: बेटियों की सुरक्षा के लिए हेल्पलाइन?\n"
            "उत्तर: महिला हेल्पलाइन: 181। बाल हेल्पलाइन: 1098।\n\n"
            "प्रश्न: बेटियों के लिए कौन सी वित्तीय योजनाएं हैं?\n"
            "उत्तर: सुकन्या समृद्धि योजना (बचत), राष्ट्रीय छात्रवृत्ति पोर्टल (शिक्षा), लाडली लक्ष्मी (राज्य योजनाएं)।"
        ),
    },
    # ── Janani Suraksha Yojana FAQs ───────────────────────────────────────
    {
        "scheme_id": "janani-suraksha-yojana",
        "section_id": "faqs",
        "category": "health",
        "name_en": "Janani Suraksha Yojana FAQs",
        "name_hi": "जननी सुरक्षा योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Janani Suraksha Yojana (JSY):\n\n"
            "Q: How much money do I get under JSY?\n"
            "A: In Low Performing States (LPS) like UP, Bihar, MP, Rajasthan etc: Rural mothers get Rs 1,400 and urban mothers get Rs 1,000. In High Performing States: Rural BPL mothers get Rs 700 and urban BPL get Rs 600.\n\n"
            "Q: When will I get the money?\n"
            "A: Money is given at the time of delivery at the hospital, or within a few days through your bank account.\n\n"
            "Q: Is there any age limit?\n"
            "A: In High Performing States, the mother must be 19 years or older. In Low Performing States, there is no age restriction.\n\n"
            "Q: Is JSY available for all pregnancies?\n"
            "A: In LPS: all institutional deliveries. In HPS: only for BPL mothers for up to 2 live births.\n\n"
            "Q: What does ASHA worker do in JSY?\n"
            "A: ASHA helps with registration, accompanies mother to hospital, arranges transport, helps with paperwork, and ensures payment. ASHA also gets Rs 600 (rural) or Rs 200 (urban) for each delivery assisted.\n\n"
            "Q: Can I use JSY at a private hospital?\n"
            "A: Only at government-accredited private hospitals. Delivery at non-accredited private hospitals is not covered.\n\n"
            "Q: What if the hospital asks for money?\n"
            "A: All services under JSY are free at government hospitals. If money is demanded, complain to the hospital superintendent, CMO, or call 1800-180-1104."
        ),
        "text_hi": (
            "जननी सुरक्षा योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: JSY में कितने पैसे मिलते हैं?\n"
            "उत्तर: कम प्रदर्शन वाले राज्यों (UP, बिहार, MP, राजस्थान आदि) में: ग्रामीण माताओं को 1,400 और शहरी को 1,000 रुपये। अधिक प्रदर्शन वाले राज्यों में: ग्रामीण BPL को 700, शहरी BPL को 600 रुपये।\n\n"
            "प्रश्न: पैसा कब मिलेगा?\n"
            "उत्तर: अस्पताल में प्रसव के समय या कुछ दिनों में बैंक खाते में।\n\n"
            "प्रश्न: क्या उम्र की सीमा है?\n"
            "उत्तर: उच्च प्रदर्शन राज्यों में 19 वर्ष या अधिक। कम प्रदर्शन राज्यों में कोई उम्र सीमा नहीं।\n\n"
            "प्रश्न: आशा कार्यकर्ता क्या करती है?\n"
            "उत्तर: पंजीकरण में मदद, अस्पताल ले जाना, परिवहन व्यवस्था, कागजी कार्रवाई और भुगतान सुनिश्चित करना। आशा को भी प्रति प्रसव 600 (ग्रामीण) या 200 (शहरी) रुपये मिलते हैं।\n\n"
            "प्रश्न: अगर अस्पताल पैसे मांगे तो?\n"
            "उत्तर: सरकारी अस्पताल में सब कुछ मुफ्त है। पैसे मांगने पर अस्पताल अधीक्षक, CMO से शिकायत करें या 1800-180-1104 पर कॉल करें।"
        ),
    },
    # ── PM Garib Kalyan Anna Yojana FAQs ──────────────────────────────────
    {
        "scheme_id": "pm-garib-kalyan-anna",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM Garib Kalyan Anna Yojana FAQs",
        "name_hi": "पीएम गरीब कल्याण अन्न योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Garib Kalyan Anna Yojana (PMGKAY):\n\n"
            "Q: How much free grain do I get?\n"
            "A: 5 kg free foodgrain per person per month. Antyodaya (AAY) families continue to get 35 kg per family per month.\n\n"
            "Q: Which grains are given?\n"
            "A: Wheat, rice, or coarse grains depending on your state's allocation. Quality must meet Food Corporation of India standards.\n\n"
            "Q: Do I need to pay anything?\n"
            "A: No, the grain is completely free under the NFSA/PMGKAY scheme. If the ration shop asks for money, it is illegal.\n\n"
            "Q: How to get a ration card?\n"
            "A: Apply at your District Food & Supply Office or online at your state's PDS portal. Documents: Aadhaar, address proof, income certificate, family details.\n\n"
            "Q: My ration card doesn't work at the Fair Price Shop. What to do?\n"
            "A: Ensure Aadhaar is seeded (linked) to your ration card. Visit the Food & Supply Office. Common issues: fingerprint mismatch - use iris scan or OTP instead.\n\n"
            "Q: Can I get ration from a different shop?\n"
            "A: Yes. Under One Nation One Ration Card (ONORC), you can collect ration from any Fair Price Shop in India using Aadhaar-based authentication.\n\n"
            "Q: Until when is free grain available?\n"
            "A: The scheme has been extended under NFSA until December 2028. All eligible families will continue to get free grain.\n\n"
            "Q: Where to complain about ration shop issues?\n"
            "A: Call 1967 (food helpline), or contact your District Food & Supply Officer, or file online at your state's PDS portal."
        ),
        "text_hi": (
            "पीएम गरीब कल्याण अन्न योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: कितना मुफ्त अनाज मिलता है?\n"
            "उत्तर: प्रति व्यक्ति प्रति माह 5 किलो मुफ्त अनाज। अंत्योदय (AAY) परिवारों को प्रति परिवार 35 किलो।\n\n"
            "प्रश्न: कौन सा अनाज मिलता है?\n"
            "उत्तर: राज्य के अनुसार गेहूं, चावल या मोटा अनाज। गुणवत्ता भारतीय खाद्य निगम के मानक अनुसार।\n\n"
            "प्रश्न: क्या कुछ पैसे देने होंगे?\n"
            "उत्तर: नहीं, अनाज पूरी तरह मुफ्त है। राशन दुकानदार पैसे मांगे तो यह गैर-कानूनी है।\n\n"
            "प्रश्न: राशन कार्ड कैसे बनवाएं?\n"
            "उत्तर: जिला खाद्य एवं आपूर्ति कार्यालय में या राज्य PDS पोर्टल पर ऑनलाइन। दस्तावेज: आधार, पता प्रमाण, आय प्रमाण पत्र, परिवार विवरण।\n\n"
            "प्रश्न: राशन कार्ड काम नहीं कर रहा, क्या करें?\n"
            "उत्तर: आधार राशन कार्ड से लिंक (सीड) करवाएं। खाद्य कार्यालय जाएं। फिंगरप्रिंट न मिले तो आइरिस स्कैन या OTP इस्तेमाल करें।\n\n"
            "प्रश्न: क्या दूसरी दुकान से राशन ले सकते हैं?\n"
            "उत्तर: हां। One Nation One Ration Card के तहत भारत की किसी भी राशन दुकान से आधार से राशन ले सकते हैं।\n\n"
            "प्रश्न: मुफ्त अनाज कब तक मिलेगा?\n"
            "उत्तर: NFSA के तहत दिसंबर 2028 तक बढ़ाई गई है।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: 1967 (खाद्य हेल्पलाइन) पर कॉल करें, या जिला खाद्य अधिकारी से मिलें, या राज्य PDS पोर्टल पर ऑनलाइन शिकायत करें।"
        ),
    },
    # ── PM Jan Dhan Yojana FAQs ───────────────────────────────────────────
    {
        "scheme_id": "pmjdy-jan-dhan",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM Jan Dhan Yojana FAQs",
        "name_hi": "पीएम जन धन योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Jan Dhan Yojana:\n\n"
            "Q: Is Jan Dhan account free?\n"
            "A: Yes. Zero balance account with free RuPay debit card. No minimum balance needed. No charges for opening.\n\n"
            "Q: What insurance comes with Jan Dhan account?\n"
            "A: Rs 2 lakh accidental death/disability insurance through RuPay card, and Rs 30,000 life insurance (for accounts opened between Aug 2014 - Jan 2015, extended for eligible accounts).\n\n"
            "Q: What is the overdraft facility?\n"
            "A: After 6 months of good account history, you can get up to Rs 10,000 overdraft (loan). One overdraft per household.\n\n"
            "Q: Can I open a Jan Dhan account if I already have a bank account?\n"
            "A: Jan Dhan is for unbanked people. If you already have an account, you cannot open another basic savings account but can convert existing account.\n\n"
            "Q: What is the minimum age?\n"
            "A: 10 years and above can open a Jan Dhan account. Minors (10-18) can open with parent/guardian co-sign.\n\n"
            "Q: Can Jan Dhan account be used to receive government scheme payments?\n"
            "A: Yes. Jan Dhan accounts are DBT (Direct Benefit Transfer) enabled. All government subsidies and payments can come to this account.\n\n"
            "Q: How to link Aadhaar with Jan Dhan account?\n"
            "A: Visit your bank branch with Aadhaar card. Fill a small form to seed/link Aadhaar. This is necessary for receiving government benefits."
        ),
        "text_hi": (
            "पीएम जन धन योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: क्या जन धन खाता मुफ्त है?\n"
            "उत्तर: हां। जीरो बैलेंस खाता, मुफ्त RuPay डेबिट कार्ड। कोई न्यूनतम बैलेंस नहीं। खोलने का कोई शुल्क नहीं।\n\n"
            "प्रश्न: जन धन खाते के साथ कौन सा बीमा मिलता है?\n"
            "उत्तर: RuPay कार्ड से 2 लाख रुपये दुर्घटना मृत्यु/विकलांगता बीमा, और 30,000 रुपये जीवन बीमा (पात्र खातों के लिए)।\n\n"
            "प्रश्न: ओवरड्राफ्ट सुविधा क्या है?\n"
            "उत्तर: 6 महीने अच्छा खाता इतिहास होने पर 10,000 रुपये तक ओवरड्राफ्ट (कर्ज) मिल सकता है। प्रति परिवार एक ओवरड्राफ्ट।\n\n"
            "प्रश्न: क्या सरकारी योजनाओं का पैसा जन धन खाते में आ सकता है?\n"
            "उत्तर: हां। जन धन खाते DBT (डायरेक्ट बेनिफिट ट्रांसफर) सक्षम हैं। सभी सरकारी सब्सिडी और भुगतान इसमें आ सकते हैं।\n\n"
            "प्रश्न: आधार कैसे लिंक करें?\n"
            "उत्तर: बैंक शाखा में आधार कार्ड लेकर जाएं। छोटा फॉर्म भरें। सरकारी लाभ पाने के लिए यह जरूरी है।"
        ),
    },
    # ── PM Ujjwala Yojana FAQs ────────────────────────────────────────────
    {
        "scheme_id": "pm-ujjwala-yojana",
        "section_id": "faqs",
        "category": "women",
        "name_en": "PM Ujjwala Yojana FAQs",
        "name_hi": "पीएम उज्ज्वला योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Ujjwala Yojana:\n\n"
            "Q: What do I get under PM Ujjwala?\n"
            "A: Free LPG gas connection, Rs 1,600 financial support for connection, free first gas refill, and a free stove. After that, you buy refills at market or subsidized rate.\n\n"
            "Q: Who can apply for Ujjwala?\n"
            "A: Adult women (18+) from BPL families, SC/ST, PMAY beneficiaries, Antyodaya, forest/island dwellers, most backward classes, and tea garden/ex-tea garden workers.\n\n"
            "Q: Can the connection be in a man's name?\n"
            "A: No. The LPG connection must be in the name of an adult woman of the household.\n\n"
            "Q: How to apply for Ujjwala?\n"
            "A: Visit nearest LPG distributor (HP, Bharat, or Indane) with Aadhaar, BPL ration card, and bank passbook. Or apply online at pmuy.gov.in.\n\n"
            "Q: I already have one LPG connection. Can I get Ujjwala?\n"
            "A: No. Ujjwala is only for households that do not have any existing LPG connection.\n\n"
            "Q: How to get LPG subsidy in my bank account?\n"
            "A: Link your Aadhaar with your bank account. Then link Aadhaar with your LPG consumer ID through your distributor. Subsidy will come directly to bank.\n\n"
            "Q: How to transfer Ujjwala connection to another address?\n"
            "A: Visit your LPG distributor with new address proof and Aadhaar. Connection can be transferred to any distributor in India.\n\n"
            "Q: Where to complain about Ujjwala issues?\n"
            "A: Call 1906 (LPG helpline) or contact your LPG distributor. For online complaints, visit mylpg.in."
        ),
        "text_hi": (
            "पीएम उज्ज्वला योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: उज्ज्वला में क्या मिलता है?\n"
            "उत्तर: मुफ्त LPG गैस कनेक्शन, कनेक्शन के लिए 1,600 रुपये, पहला गैस रिफिल मुफ्त और मुफ्त चूल्हा। उसके बाद बाजार या सब्सिडी दर पर रिफिल खरीदें।\n\n"
            "प्रश्न: कौन आवेदन कर सकता है?\n"
            "उत्तर: BPL परिवारों, SC/ST, PMAY लाभार्थियों, अंत्योदय, वन/द्वीप निवासियों, अत्यंत पिछड़ी जातियों की वयस्क महिलाएं (18+)।\n\n"
            "प्रश्न: क्या पुरुष के नाम पर कनेक्शन मिलेगा?\n"
            "उत्तर: नहीं। LPG कनेक्शन घर की वयस्क महिला के नाम पर ही होगा।\n\n"
            "प्रश्न: आवेदन कैसे करें?\n"
            "उत्तर: नजदीकी LPG वितरक (HP, भारत या इंडेन) के पास आधार, BPL राशन कार्ड और बैंक पासबुक लेकर जाएं। या pmuy.gov.in पर ऑनलाइन।\n\n"
            "प्रश्न: LPG सब्सिडी बैंक में कैसे आएगी?\n"
            "उत्तर: आधार को बैंक खाते से लिंक करें। फिर वितरक के माध्यम से आधार को LPG कंज्यूमर ID से लिंक करें।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: 1906 (LPG हेल्पलाइन) पर कॉल करें या LPG वितरक से संपर्क करें। ऑनलाइन: mylpg.in।"
        ),
    },
    # ── National Scholarship Portal FAQs ──────────────────────────────────
    {
        "scheme_id": "national-scholarship-portal",
        "section_id": "faqs",
        "category": "education",
        "name_en": "National Scholarship Portal FAQs",
        "name_hi": "राष्ट्रीय छात्रवृत्ति पोर्टल अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about National Scholarship Portal:\n\n"
            "Q: What scholarships are available on NSP?\n"
            "A: Pre-matric, post-matric, top-class, merit-cum-means, and special scholarships for SC, ST, OBC, minorities, and disabled students.\n\n"
            "Q: How much scholarship money can I get?\n"
            "A: Varies by scholarship: Rs 1,500 to Rs 20,000+ per year. Some cover full tuition fees, hostel, and maintenance allowance.\n\n"
            "Q: When is the NSP application deadline?\n"
            "A: Typically opens by August-September and closes by November-December each year. Check scholarships.gov.in for exact dates.\n\n"
            "Q: How to apply on NSP?\n"
            "A: Register at scholarships.gov.in > create OTR (One-Time Registration) > log in > select scholarship > fill form > upload documents > submit. Institute must verify the application.\n\n"
            "Q: How to check scholarship application status?\n"
            "A: Login at scholarships.gov.in > Check Status, or contact your institution's scholarship nodal officer.\n\n"
            "Q: When do I receive the scholarship money?\n"
            "A: After verification by institute, state, and central level. Usually within 3-6 months of application. Money goes directly to bank account via DBT.\n\n"
            "Q: My scholarship renewal was rejected. Why?\n"
            "A: Common reasons: low attendance, failed exams, income increased, documents expired. Re-apply with updated documents next year.\n\n"
            "Q: Can I apply for multiple scholarships?\n"
            "A: Generally no. You can apply for one central and one state scholarship. Cannot receive two central scholarships simultaneously."
        ),
        "text_hi": (
            "राष्ट्रीय छात्रवृत्ति पोर्टल के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: NSP पर कौन सी छात्रवृत्तियां हैं?\n"
            "उत्तर: प्री-मैट्रिक, पोस्ट-मैट्रिक, टॉप-क्लास, मेरिट-कम-मीन्स, और SC, ST, OBC, अल्पसंख्यक, दिव्यांग छात्रों के लिए विशेष छात्रवृत्तियां।\n\n"
            "प्रश्न: कितने पैसे मिलते हैं?\n"
            "उत्तर: छात्रवृत्ति अनुसार 1,500 से 20,000+ रुपये सालाना। कुछ में पूरी ट्यूशन फीस, हॉस्टल और मेंटेनेंस भत्ता शामिल।\n\n"
            "प्रश्न: NSP आवेदन की अंतिम तिथि कब है?\n"
            "उत्तर: आमतौर पर अगस्त-सितंबर में खुलता है और नवंबर-दिसंबर में बंद। scholarships.gov.in पर सही तारीख देखें।\n\n"
            "प्रश्न: NSP पर आवेदन कैसे करें?\n"
            "उत्तर: scholarships.gov.in पर पंजीकरण > OTR बनाएं > लॉगिन > छात्रवृत्ति चुनें > फॉर्म भरें > दस्तावेज अपलोड > जमा करें। संस्थान को सत्यापित करना होगा।\n\n"
            "प्रश्न: छात्रवृत्ति का पैसा कब मिलता है?\n"
            "उत्तर: संस्थान, राज्य और केंद्र स्तर पर सत्यापन के बाद। आमतौर पर आवेदन के 3-6 महीने में। DBT से सीधे बैंक खाते में।\n\n"
            "प्रश्न: क्या एक साथ कई छात्रवृत्ति ले सकते हैं?\n"
            "उत्तर: आमतौर पर नहीं। एक केंद्रीय और एक राज्य छात्रवृत्ति ले सकते हैं। दो केंद्रीय छात्रवृत्तियां एक साथ नहीं।"
        ),
    },
    # ── Soil Health Card FAQs ─────────────────────────────────────────────
    {
        "scheme_id": "soil-health-card",
        "section_id": "faqs",
        "category": "agriculture",
        "name_en": "Soil Health Card Scheme FAQs",
        "name_hi": "मृदा स्वास्थ्य कार्ड योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Soil Health Card:\n\n"
            "Q: What information does the Soil Health Card give?\n"
            "A: It tells the status of 12 parameters: pH, Electrical Conductivity, Organic Carbon, Nitrogen, Phosphorus, Potassium, Sulphur, Zinc, Iron, Copper, Manganese, and Boron. It also recommends which fertilizers and how much to use.\n\n"
            "Q: Is Soil Health Card free?\n"
            "A: Yes, completely free. No charges for soil testing or card issuance.\n\n"
            "Q: How often is the card issued?\n"
            "A: Every 2 years (once in a crop cycle of 2 years).\n\n"
            "Q: How to get a Soil Health Card?\n"
            "A: Contact your Krishi Vigyan Kendra, local agriculture officer, or register at soilhealth.dac.gov.in. A soil sample collector will visit your farm.\n\n"
            "Q: How to check my Soil Health Card online?\n"
            "A: Visit soilhealth.dac.gov.in > Enter your state, district, and details to view your card and recommendations.\n\n"
            "Q: Does following the card really improve crops?\n"
            "A: Yes. Studies show farmers who follow Soil Health Card recommendations save 10-15% on fertilizer costs and improve crop yield by 10-20%."
        ),
        "text_hi": (
            "मृदा स्वास्थ्य कार्ड योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: कार्ड में क्या जानकारी मिलती है?\n"
            "उत्तर: 12 मापदंडों की स्थिति: pH, विद्युत चालकता, जैविक कार्बन, नाइट्रोजन, फॉस्फोरस, पोटैशियम, सल्फर, जिंक, आयरन, कॉपर, मैंगनीज, बोरॉन। साथ में कौन सी खाद कितनी डालें, यह भी बताता है।\n\n"
            "प्रश्न: क्या कार्ड मुफ्त है?\n"
            "उत्तर: हां, पूरी तरह मुफ्त। मिट्टी जांच या कार्ड बनाने का कोई शुल्क नहीं।\n\n"
            "प्रश्न: कार्ड कितने समय में मिलता है?\n"
            "उत्तर: हर 2 साल में एक बार (2 साल के फसल चक्र में एक बार)।\n\n"
            "प्रश्न: कार्ड कैसे प्राप्त करें?\n"
            "उत्तर: कृषि विज्ञान केंद्र, स्थानीय कृषि अधिकारी से संपर्क करें, या soilhealth.dac.gov.in पर पंजीकरण करें।\n\n"
            "प्रश्न: क्या कार्ड की सिफारिश से सच में फसल बेहतर होती है?\n"
            "उत्तर: हां। अध्ययन बताते हैं कि सिफारिशें मानने वाले किसान खाद पर 10-15% बचत करते हैं और उपज 10-20% बढ़ती है।"
        ),
    },
    # ── PM POSHAN (Mid-Day Meal) FAQs ─────────────────────────────────────
    {
        "scheme_id": "pm-poshan-mid-day-meal",
        "section_id": "faqs",
        "category": "education",
        "name_en": "PM POSHAN (Mid-Day Meal) FAQs",
        "name_hi": "पीएम पोषण (मध्याह्न भोजन) अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM POSHAN:\n\n"
            "Q: Who gets mid-day meal?\n"
            "A: All children enrolled in government, government-aided, and local body schools from class 1 to 8. Also covers children in EGS and AIE centres.\n\n"
            "Q: What food is given?\n"
            "A: A cooked meal with rice/wheat, dal, vegetables, and oil. Eggs, fruits, or milk are added depending on the state. Menu varies regionally.\n\n"
            "Q: How many calories does the meal provide?\n"
            "A: Primary (class 1-5): 450 calories and 12g protein. Upper primary (class 6-8): 700 calories and 20g protein.\n\n"
            "Q: Is the meal given on holidays?\n"
            "A: No. Meals are served only on school working days. During COVID, food security allowance (grain + money) was given instead.\n\n"
            "Q: What if the food quality is bad?\n"
            "A: Complain to the school headmaster, Block Education Officer, or call 1800-180-5727. Quality monitoring committees exist at school and block level.\n\n"
            "Q: Does PM POSHAN give money to parents?\n"
            "A: Generally no. It provides cooked meals at school. However, during special circumstances food security allowance may be given."
        ),
        "text_hi": (
            "पीएम पोषण के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: मध्याह्न भोजन किसे मिलता है?\n"
            "उत्तर: सरकारी, सरकारी सहायता प्राप्त और स्थानीय निकाय के स्कूलों में कक्षा 1 से 8 के सभी बच्चों को।\n\n"
            "प्रश्न: क्या खाना मिलता है?\n"
            "उत्तर: चावल/गेहूं, दाल, सब्जी और तेल से बना पका भोजन। राज्य के अनुसार अंडे, फल या दूध भी।\n\n"
            "प्रश्न: कितनी कैलोरी मिलती है?\n"
            "उत्तर: प्राथमिक (कक्षा 1-5): 450 कैलोरी और 12 ग्राम प्रोटीन। उच्च प्राथमिक (कक्षा 6-8): 700 कैलोरी और 20 ग्राम प्रोटीन।\n\n"
            "प्रश्न: खाने की गुणवत्ता खराब हो तो?\n"
            "उत्तर: स्कूल प्रधानाध्यापक, खंड शिक्षा अधिकारी से शिकायत करें या 1800-180-5727 पर कॉल करें।"
        ),
    },
    # ── Mahila Samman Savings Certificate FAQs ────────────────────────────
    {
        "scheme_id": "mahila-samman-savings",
        "section_id": "faqs",
        "category": "women",
        "name_en": "Mahila Samman Savings Certificate FAQs",
        "name_hi": "महिला सम्मान बचत प्रमाणपत्र अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Mahila Samman Savings Certificate:\n\n"
            "Q: What is the interest rate?\n"
            "A: 7.5% per annum, compounded quarterly. This is higher than most fixed deposits.\n\n"
            "Q: What is the minimum and maximum deposit?\n"
            "A: Minimum Rs 1,000, maximum Rs 2 lakh. You can open multiple accounts but total across all institutions cannot exceed Rs 2 lakh.\n\n"
            "Q: When does the account mature?\n"
            "A: After 2 years from the date of opening. You get the full amount plus interest on maturity.\n\n"
            "Q: Can I withdraw money before 2 years?\n"
            "A: Yes. Partial withdrawal of up to 40% of the balance is allowed after 1 year. Full premature closure is also possible with slightly lower interest.\n\n"
            "Q: Where can I open this account?\n"
            "A: At any post office or authorized bank branch.\n\n"
            "Q: Is there a tax benefit?\n"
            "A: Interest income is taxable. However, there is no TDS if total interest is below Rs 40,000.\n\n"
            "Q: Can a man open this account?\n"
            "A: The account must be in a woman's or girl's name. A man can open it as guardian for a minor girl, but the account holder must be female."
        ),
        "text_hi": (
            "महिला सम्मान बचत प्रमाणपत्र के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: ब्याज दर क्या है?\n"
            "उत्तर: 7.5% सालाना, तिमाही चक्रवृद्धि। यह अधिकतर फिक्स्ड डिपॉजिट से ज्यादा है।\n\n"
            "प्रश्न: न्यूनतम और अधिकतम जमा कितनी है?\n"
            "उत्तर: न्यूनतम 1,000 रुपये, अधिकतम 2 लाख रुपये।\n\n"
            "प्रश्न: खाता कब परिपक्व होता है?\n"
            "उत्तर: खोलने की तारीख से 2 साल बाद। परिपक्वता पर पूरी राशि और ब्याज मिलता है।\n\n"
            "प्रश्न: क्या 2 साल से पहले पैसे निकाल सकते हैं?\n"
            "उत्तर: हां। 1 साल बाद 40% तक आंशिक निकासी की अनुमति है।\n\n"
            "प्रश्न: कहां खाता खोलें?\n"
            "उत्तर: किसी भी डाकघर या अधिकृत बैंक शाखा में।\n\n"
            "प्रश्न: क्या पुरुष यह खाता खोल सकता है?\n"
            "उत्तर: खाता महिला या लड़की के नाम पर होना चाहिए। पुरुष नाबालिग लड़की के अभिभावक के रूप में खोल सकता है।"
        ),
    },
    # ── PM Kaushal Vikas Yojana FAQs ──────────────────────────────────────
    {
        "scheme_id": "pm-kaushal-vikas",
        "section_id": "faqs",
        "category": "education",
        "name_en": "PM Kaushal Vikas Yojana FAQs",
        "name_hi": "पीएम कौशल विकास योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Kaushal Vikas Yojana (PMKVY):\n\n"
            "Q: Is PMKVY training free?\n"
            "A: Yes. Training, assessment, and certification are completely free. You also get a small stipend during training.\n\n"
            "Q: What courses are available?\n"
            "A: Over 300 courses in sectors like IT, retail, beauty, healthcare, automotive, construction, electrician, plumber, welding, tailoring, food processing etc.\n\n"
            "Q: How long is the training?\n"
            "A: Short-term training: 150-300 hours (2-3 months). Recognition of Prior Learning: for those already working, assessment-based certification in a few days.\n\n"
            "Q: Will I get a job after training?\n"
            "A: PMKVY aims for at least 70% placement rate. Training centres provide placement assistance. But job is not guaranteed.\n\n"
            "Q: What is the minimum education needed?\n"
            "A: Varies by course. Many courses accept 8th pass or 10th pass. Some have no educational requirement.\n\n"
            "Q: How to find a PMKVY training centre near me?\n"
            "A: Visit pmkvyofficial.org > Find a Training Centre > enter your state, district, and sector.\n\n"
            "Q: Do I get a certificate after training?\n"
            "A: Yes. NSQF (National Skills Qualifications Framework) aligned certificate from the Sector Skill Council. Recognized by industry.\n\n"
            "Q: What is the age limit for PMKVY?\n"
            "A: Generally 15-45 years, but varies by specific course and training partner."
        ),
        "text_hi": (
            "पीएम कौशल विकास योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: क्या PMKVY प्रशिक्षण मुफ्त है?\n"
            "उत्तर: हां। प्रशिक्षण, मूल्यांकन और प्रमाणन पूरी तरह मुफ्त। प्रशिक्षण के दौरान छोटा भत्ता भी मिलता है।\n\n"
            "प्रश्न: कौन से कोर्स उपलब्ध हैं?\n"
            "उत्तर: IT, रिटेल, ब्यूटी, स्वास्थ्य, ऑटोमोटिव, निर्माण, इलेक्ट्रीशियन, प्लंबर, वेल्डिंग, सिलाई, फूड प्रोसेसिंग सहित 300+ कोर्स।\n\n"
            "प्रश्न: प्रशिक्षण कितने दिन का होता है?\n"
            "उत्तर: शॉर्ट-टर्म: 150-300 घंटे (2-3 महीने)। RPL: पहले से काम करने वालों के लिए कुछ दिनों में मूल्यांकन-आधारित प्रमाणन।\n\n"
            "प्रश्न: क्या ट्रेनिंग के बाद नौकरी मिलेगी?\n"
            "उत्तर: PMKVY का लक्ष्य 70% प्लेसमेंट है। केंद्र प्लेसमेंट में मदद करते हैं। लेकिन नौकरी की गारंटी नहीं।\n\n"
            "प्रश्न: नजदीकी प्रशिक्षण केंद्र कैसे खोजें?\n"
            "उत्तर: pmkvyofficial.org > Find a Training Centre > राज्य, जिला और सेक्टर चुनें।\n\n"
            "प्रश्न: क्या सर्टिफिकेट मिलता है?\n"
            "उत्तर: हां। NSQF अनुरूप सेक्टर स्किल काउंसिल का प्रमाणपत्र। उद्योग द्वारा मान्यता प्राप्त।"
        ),
    },
    # ── PM Suraksha Bima Yojana FAQs ──────────────────────────────────────
    {
        "scheme_id": "pm-suraksha-bima",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM Suraksha Bima Yojana FAQs",
        "name_hi": "पीएम सुरक्षा बीमा योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Suraksha Bima Yojana (PMSBY):\n\n"
            "Q: How much does PMSBY cost?\n"
            "A: Only Rs 20 per year (less than Rs 2 per month). Auto-debited from bank account once a year.\n\n"
            "Q: What does PMSBY cover?\n"
            "A: Accidental death: Rs 2 lakh. Total permanent disability: Rs 2 lakh. Partial permanent disability: Rs 1 lakh. Only accident-related claims, not natural death.\n\n"
            "Q: How to claim PMSBY insurance?\n"
            "A: In case of accident, inform your bank. Submit claim form, FIR copy, hospital records, disability certificate, and nominee's bank details. Bank processes the claim.\n\n"
            "Q: Can I have PMSBY from multiple bank accounts?\n"
            "A: No. Only one PMSBY enrollment per person, through one bank account.\n\n"
            "Q: What is the coverage period?\n"
            "A: June 1 to May 31 each year. Premium is debited around May-June. You must keep sufficient balance in the account.\n\n"
            "Q: Does PMSBY cover natural death?\n"
            "A: No. PMSBY covers only accidental death and disability. For life insurance (any cause of death), take PMJJBY instead.\n\n"
            "Q: What is the age limit?\n"
            "A: 18 to 70 years."
        ),
        "text_hi": (
            "पीएम सुरक्षा बीमा योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: PMSBY की कीमत कितनी है?\n"
            "उत्तर: सिर्फ 20 रुपये सालाना (2 रुपये/माह से भी कम)। बैंक खाते से साल में एक बार ऑटो-डेबिट।\n\n"
            "प्रश्न: PMSBY में क्या कवर होता है?\n"
            "उत्तर: दुर्घटना मृत्यु: 2 लाख। पूर्ण स्थायी विकलांगता: 2 लाख। आंशिक स्थायी विकलांगता: 1 लाख। केवल दुर्घटना, प्राकृतिक मृत्यु कवर नहीं।\n\n"
            "प्रश्न: बीमा दावा कैसे करें?\n"
            "उत्तर: दुर्घटना होने पर बैंक को सूचित करें। दावा फॉर्म, FIR, अस्पताल रिकॉर्ड, विकलांगता प्रमाण पत्र और नॉमिनी की बैंक जानकारी जमा करें।\n\n"
            "प्रश्न: क्या PMSBY प्राकृतिक मृत्यु कवर करता है?\n"
            "उत्तर: नहीं। PMSBY केवल दुर्घटना कवर करता है। जीवन बीमा (किसी भी कारण) के लिए PMJJBY लें।\n\n"
            "प्रश्न: उम्र सीमा क्या है?\n"
            "उत्तर: 18 से 70 वर्ष।"
        ),
    },
    # ── PM Jeevan Jyoti Bima Yojana FAQs ─────────────────────────────────
    {
        "scheme_id": "pm-jeevan-jyoti-bima",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM Jeevan Jyoti Bima Yojana FAQs",
        "name_hi": "पीएम जीवन ज्योति बीमा योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Jeevan Jyoti Bima Yojana (PMJJBY):\n\n"
            "Q: How much does PMJJBY cost?\n"
            "A: Rs 436 per year. Auto-debited from bank account once a year.\n\n"
            "Q: What does PMJJBY cover?\n"
            "A: Rs 2 lakh to nominee on death of the insured person from ANY cause - accident, natural death, illness, any reason.\n\n"
            "Q: What is the difference between PMJJBY and PMSBY?\n"
            "A: PMJJBY covers death from any cause (Rs 436/year, Rs 2 lakh cover). PMSBY covers only accidental death/disability (Rs 20/year, Rs 2 lakh cover). You can take both.\n\n"
            "Q: How to claim PMJJBY insurance?\n"
            "A: Nominee must inform the bank within 30 days of death. Submit claim form, death certificate, nominee's Aadhaar and bank details. Claim settled within 30 days.\n\n"
            "Q: What is the age limit?\n"
            "A: 18 to 55 years to join. Coverage continues until age 55. Must renew every year.\n\n"
            "Q: Can I take both PMJJBY and PMSBY?\n"
            "A: Yes. You can take both for comprehensive coverage. Together they cost only Rs 456/year and give Rs 4 lakh total coverage.\n\n"
            "Q: Is medical examination required?\n"
            "A: No. No medical examination or health declaration needed. Simple self-declaration at the time of enrollment."
        ),
        "text_hi": (
            "पीएम जीवन ज्योति बीमा योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: PMJJBY की कीमत कितनी है?\n"
            "उत्तर: 436 रुपये सालाना। बैंक खाते से साल में एक बार ऑटो-डेबिट।\n\n"
            "प्रश्न: PMJJBY में क्या कवर होता है?\n"
            "उत्तर: बीमित व्यक्ति की किसी भी कारण से मृत्यु पर नॉमिनी को 2 लाख रुपये - दुर्घटना, प्राकृतिक मृत्यु, बीमारी, कोई भी कारण।\n\n"
            "प्रश्न: PMJJBY और PMSBY में क्या फर्क है?\n"
            "उत्तर: PMJJBY किसी भी कारण से मृत्यु कवर करता है (436/वर्ष, 2 लाख)। PMSBY सिर्फ दुर्घटना (20/वर्ष, 2 लाख)। दोनों ले सकते हैं।\n\n"
            "प्रश्न: बीमा दावा कैसे करें?\n"
            "उत्तर: नॉमिनी मृत्यु के 30 दिन में बैंक को सूचित करें। दावा फॉर्म, मृत्यु प्रमाण पत्र, नॉमिनी का आधार और बैंक जानकारी जमा करें।\n\n"
            "प्रश्न: क्या दोनों PMJJBY और PMSBY ले सकते हैं?\n"
            "उत्तर: हां। दोनों मिलाकर सिर्फ 456 रुपये/वर्ष में 4 लाख तक का कवर।\n\n"
            "प्रश्न: क्या मेडिकल जांच चाहिए?\n"
            "उत्तर: नहीं। कोई मेडिकल जांच या स्वास्थ्य घोषणा नहीं। नामांकन के समय साधारण स्व-घोषणा।"
        ),
    },
    # ── Stand Up India FAQs ───────────────────────────────────────────────
    {
        "scheme_id": "stand-up-india",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "Stand Up India FAQs",
        "name_hi": "स्टैंड अप इंडिया अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Stand Up India:\n\n"
            "Q: How much loan can I get?\n"
            "A: Rs 10 lakh to Rs 1 crore for setting up a new enterprise in manufacturing, services, or trading.\n\n"
            "Q: Who is eligible?\n"
            "A: SC/ST and/or women entrepreneurs aged 18+ who are setting up a FIRST-TIME greenfield (new) enterprise. Not for existing businesses.\n\n"
            "Q: What is the interest rate?\n"
            "A: Base rate of the bank + tenure premium + 3%, or slightly lower. Not fixed - varies by bank.\n\n"
            "Q: Do I need to give collateral?\n"
            "A: Loan is secured by the asset created (equipment, property). Additional collateral through CGTMSE guarantee if needed.\n\n"
            "Q: What is the repayment period?\n"
            "A: Up to 7 years, with a moratorium (grace period) of up to 18 months.\n\n"
            "Q: Where to apply?\n"
            "A: Register at standupmitra.in, or apply directly at any scheduled commercial bank branch. Each bank branch must fund at least one SC/ST and one woman entrepreneur.\n\n"
            "Q: My bank refused the loan. What should I do?\n"
            "A: Login at standupmitra.in and connect with a SIDBI handholding agency. You can also approach the Lead District Manager or District Level Review Committee.\n\n"
            "Q: Can I take Stand Up India loan for an existing business?\n"
            "A: No. Stand Up India is only for greenfield (new) enterprises. For existing business expansion, apply under MUDRA or other schemes."
        ),
        "text_hi": (
            "स्टैंड अप इंडिया के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: कितना लोन मिलता है?\n"
            "उत्तर: विनिर्माण, सेवा या व्यापार में नया उद्यम शुरू करने के लिए 10 लाख से 1 करोड़ रुपये।\n\n"
            "प्रश्न: कौन पात्र है?\n"
            "उत्तर: 18+ उम्र के SC/ST और/या महिला उद्यमी जो पहली बार नया उद्यम शुरू कर रहे हों।\n\n"
            "प्रश्न: चुकौती अवधि कितनी है?\n"
            "उत्तर: 7 साल तक, 18 महीने तक की छूट अवधि (मोरेटोरियम) के साथ।\n\n"
            "प्रश्न: कहां आवेदन करें?\n"
            "उत्तर: standupmitra.in पर पंजीकरण करें, या किसी भी बैंक शाखा में सीधे। हर बैंक शाखा को कम से कम एक SC/ST और एक महिला को कर्ज देना होता है।\n\n"
            "प्रश्न: बैंक ने लोन से मना कर दिया, क्या करें?\n"
            "उत्तर: standupmitra.in पर SIDBI हैंडहोल्डिंग एजेंसी से जुड़ें। जिला अग्रणी प्रबंधक या जिला स्तरीय समीक्षा समिति से संपर्क करें।\n\n"
            "प्रश्न: क्या मौजूदा बिजनेस के लिए लोन मिलेगा?\n"
            "उत्तर: नहीं। सिर्फ नए उद्यम के लिए। मौजूदा बिजनेस विस्तार के लिए मुद्रा या अन्य योजनाओं में आवेदन करें।"
        ),
    },
    # ── PM Matru Vandana Yojana FAQs ──────────────────────────────────────
    {
        "scheme_id": "pm-matru-vandana",
        "section_id": "faqs",
        "category": "women",
        "name_en": "PM Matru Vandana Yojana FAQs",
        "name_hi": "पीएम मातृ वंदना योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Matru Vandana Yojana (PMMVY):\n\n"
            "Q: How much money do I get?\n"
            "A: First child: Rs 5,000 in 3 installments. Second child (if girl): Rs 6,000 in 2 installments. An additional Rs 1,000 if born in a hospital (Janani Suraksha Yojana).\n\n"
            "Q: When do the installments come?\n"
            "A: First child: 1st installment (Rs 3,000) at pregnancy registration, 2nd (Rs 1,000) after 6 months, 3rd (Rs 1,000) after child's first vaccination cycle. Second child (girl): Rs 3,000 after birth + Rs 3,000 after 6 months.\n\n"
            "Q: Where to register?\n"
            "A: At the nearest Anganwadi centre or government health facility. ASHA worker and Anganwadi worker will help with registration.\n\n"
            "Q: What documents are needed?\n"
            "A: Aadhaar card, bank passbook (linked to Aadhaar), MCP card, pregnancy registration proof, hospital birth certificate.\n\n"
            "Q: Is PMMVY available for all pregnancies?\n"
            "A: First child: available for all. Second child benefit only if the child is a girl. Not available for third or higher pregnancies.\n\n"
            "Q: How to check PMMVY payment status?\n"
            "A: Ask your Anganwadi worker, or contact the District Women & Child Development Officer, or call Women Helpline 181.\n\n"
            "Q: What if I had a miscarriage or stillbirth?\n"
            "A: You can still avail benefits for the next pregnancy as a 'first eligible pregnancy' in the scheme."
        ),
        "text_hi": (
            "पीएम मातृ वंदना योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: कितने पैसे मिलते हैं?\n"
            "उत्तर: पहला बच्चा: 3 किस्तों में 5,000 रुपये। दूसरा बच्चा (बेटी): 2 किस्तों में 6,000 रुपये। अस्पताल में जन्म पर जननी सुरक्षा योजना से 1,000 रुपये अतिरिक्त।\n\n"
            "प्रश्न: किस्तें कब आती हैं?\n"
            "उत्तर: पहला बच्चा: 1st (3,000) गर्भावस्था पंजीकरण पर, 2nd (1,000) 6 महीने बाद, 3rd (1,000) बच्चे के पहले टीकाकरण चक्र बाद। दूसरा बच्चा (बेटी): जन्म बाद 3,000 + 6 महीने बाद 3,000।\n\n"
            "प्रश्न: पंजीकरण कहां करवाएं?\n"
            "उत्तर: नजदीकी आंगनवाड़ी केंद्र या सरकारी स्वास्थ्य केंद्र में। आशा और आंगनवाड़ी कार्यकर्ता मदद करेंगी।\n\n"
            "प्रश्न: क्या सभी गर्भावस्था के लिए मिलता है?\n"
            "उत्तर: पहला बच्चा: सभी के लिए। दूसरे बच्चे का लाभ सिर्फ बेटी होने पर। तीसरे या उससे अधिक के लिए नहीं।\n\n"
            "प्रश्न: भुगतान स्थिति कैसे जांचें?\n"
            "उत्तर: आंगनवाड़ी कार्यकर्ता से पूछें, या जिला महिला एवं बाल विकास अधिकारी से, या 181 पर कॉल करें।"
        ),
    },
    # ── National Family Benefit Scheme FAQs ───────────────────────────────
    {
        "scheme_id": "national-family-benefit",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "National Family Benefit Scheme FAQs",
        "name_hi": "राष्ट्रीय परिवार लाभ योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about National Family Benefit Scheme (NFBS):\n\n"
            "Q: How much money does the family get?\n"
            "A: Rs 20,000 one-time lump sum to the surviving members of a BPL family. Some states give higher amounts - check with your state.\n\n"
            "Q: Who is the primary breadwinner?\n"
            "A: The person whose earnings are the single largest source of income for the family, whether male or female.\n\n"
            "Q: What is the age limit for the deceased?\n"
            "A: The deceased primary breadwinner must have been between 18 and 59 years of age. Not available if the breadwinner was 60 or older.\n\n"
            "Q: Cause of death matters?\n"
            "A: No. Any cause of death qualifies - natural, accident, illness, or any other reason.\n\n"
            "Q: How to apply?\n"
            "A: Apply at the District Social Welfare Office with death certificate, BPL card, Aadhaar, family details, and bank passbook. Some states allow online application through NSAP portal.\n\n"
            "Q: How long does it take to receive the money?\n"
            "A: Within 4 weeks of application as per guidelines. Actual time may vary by state - typically 1-3 months.\n\n"
            "Q: Where to complain if payment is delayed?\n"
            "A: Contact the District Social Welfare Officer, or call 1800-111-555, or file complaint on the NSAP portal (nsap.nic.in)."
        ),
        "text_hi": (
            "राष्ट्रीय परिवार लाभ योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: परिवार को कितना पैसा मिलता है?\n"
            "उत्तर: बीपीएल परिवार के जीवित सदस्यों को 20,000 रुपये एकमुश्त। कुछ राज्य अधिक देते हैं - अपने राज्य से जांचें।\n\n"
            "प्रश्न: मुख्य कमाने वाला कौन माना जाता है?\n"
            "उत्तर: जिसकी कमाई परिवार की आय का सबसे बड़ा स्रोत हो, चाहे पुरुष हो या महिला।\n\n"
            "प्रश्न: मृतक की उम्र सीमा क्या है?\n"
            "उत्तर: मुख्य कमाने वाले की उम्र 18-59 वर्ष होनी चाहिए। 60 या अधिक उम्र पर यह योजना लागू नहीं।\n\n"
            "प्रश्न: मृत्यु का कारण मायने रखता है?\n"
            "उत्तर: नहीं। किसी भी कारण से मृत्यु - प्राकृतिक, दुर्घटना, बीमारी, कोई भी कारण।\n\n"
            "प्रश्न: आवेदन कैसे करें?\n"
            "उत्तर: जिला समाज कल्याण कार्यालय में मृत्यु प्रमाण पत्र, BPL कार्ड, आधार, परिवार विवरण और बैंक पासबुक लेकर जाएं।\n\n"
            "प्रश्न: पैसा कब तक मिलता है?\n"
            "उत्तर: नियमानुसार आवेदन के 4 सप्ताह में। वास्तव में 1-3 महीने लग सकते हैं।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: जिला समाज कल्याण अधिकारी से, 1800-111-555 पर, या nsap.nic.in पर ऑनलाइन शिकायत करें।"
        ),
    },
    # ── Samagra Shiksha FAQs ──────────────────────────────────────────────
    {
        "scheme_id": "samagra-shiksha",
        "section_id": "faqs",
        "category": "education",
        "name_en": "Samagra Shiksha Abhiyan FAQs",
        "name_hi": "समग्र शिक्षा अभियान अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Samagra Shiksha Abhiyan:\n\n"
            "Q: What does Samagra Shiksha give to students?\n"
            "A: Free textbooks, uniforms (Rs 600 per child per year), transport allowance for disabled children (Rs 3,000/year), and school grants for maintenance and learning materials.\n\n"
            "Q: Does it cover private school students?\n"
            "A: No. Only students in government, government-aided, and local body schools.\n\n"
            "Q: What about girls' education?\n"
            "A: Special provisions: Kasturba Gandhi Balika Vidyalayas (residential schools for girls), self-defence training, separate toilets, menstrual hygiene support.\n\n"
            "Q: What does it do for disabled children?\n"
            "A: Rs 3,500/year per child for assistive devices, transport allowance, home-based education if needed, barrier-free school buildings.\n\n"
            "Q: How to access benefits?\n"
            "A: No application needed. Benefits flow through schools automatically. Talk to the school headmaster or District Education Office.\n\n"
            "Q: Where to complain about missing benefits?\n"
            "A: Contact Block Education Officer, District Education Officer, or call 1800-111-001."
        ),
        "text_hi": (
            "समग्र शिक्षा अभियान के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: छात्रों को क्या मिलता है?\n"
            "उत्तर: मुफ्त किताबें, वर्दी (600 रुपये/बच्चा/वर्ष), दिव्यांग बच्चों को परिवहन भत्ता (3,000/वर्ष), और स्कूल अनुदान।\n\n"
            "प्रश्न: क्या प्राइवेट स्कूल के छात्रों को मिलता है?\n"
            "उत्तर: नहीं। केवल सरकारी, सरकारी सहायता प्राप्त और स्थानीय निकाय के स्कूलों के छात्रों को।\n\n"
            "प्रश्न: लड़कियों की शिक्षा के लिए क्या है?\n"
            "उत्तर: कस्तूरबा गांधी बालिका विद्यालय (आवासीय), आत्मरक्षा प्रशिक्षण, अलग शौचालय, मासिक धर्म स्वच्छता सहायता।\n\n"
            "प्रश्न: दिव्यांग बच्चों के लिए क्या है?\n"
            "उत्तर: 3,500/वर्ष सहायक उपकरणों के लिए, परिवहन भत्ता, घर-आधारित शिक्षा, बाधा-मुक्त भवन।\n\n"
            "प्रश्न: लाभ कैसे मिलें?\n"
            "उत्तर: कोई आवेदन नहीं। स्कूलों के माध्यम से स्वचालित। प्रधानाध्यापक या जिला शिक्षा कार्यालय से बात करें।"
        ),
    },
    # ── Rashtriya Bal Swasthya Karyakram FAQs ─────────────────────────────
    {
        "scheme_id": "rashtriya-bal-swasthya",
        "section_id": "faqs",
        "category": "health",
        "name_en": "Rashtriya Bal Swasthya Karyakram FAQs",
        "name_hi": "राष्ट्रीय बाल स्वास्थ्य कार्यक्रम अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about RBSK:\n\n"
            "Q: What does RBSK screen for?\n"
            "A: 4 Ds: (1) Defects at birth (cleft lip, club foot, heart defects), (2) Diseases (skin, ear, eye, dental, anemia), (3) Deficiencies (malnutrition, vitamin D, iron), (4) Development delays (learning disabilities, speech delays, autism, vision/hearing problems).\n\n"
            "Q: Is RBSK treatment free?\n"
            "A: Yes. Screening, referral, and treatment all free at government hospitals. Includes free surgery for birth defects.\n\n"
            "Q: Where does screening happen?\n"
            "A: At government schools and Anganwadi centres. RBSK mobile health teams (2 trained personnel per team) visit regularly.\n\n"
            "Q: What is the age range?\n"
            "A: Birth to 18 years. Newborn screening at government hospitals, then periodic screening at Anganwadis and schools.\n\n"
            "Q: Do I need to register my child?\n"
            "A: No registration needed. RBSK teams visit schools and Anganwadis automatically. For referral treatment, go to the nearest CHC or district hospital.\n\n"
            "Q: Where to go for treatment if RBSK finds a problem?\n"
            "A: The RBSK team refers to CHC, district hospital, or tertiary care hospital depending on severity. All treatment is free."
        ),
        "text_hi": (
            "राष्ट्रीय बाल स्वास्थ्य कार्यक्रम के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: RBSK में किन चीजों की जांच होती है?\n"
            "उत्तर: 4D: (1) जन्मजात दोष (कटा होंठ, क्लब फुट, हृदय दोष), (2) बीमारियां (त्वचा, कान, आंख, दांत, एनीमिया), (3) कमियां (कुपोषण, विटामिन D, आयरन), (4) विकास में देरी (सीखने में कठिनाई, बोलने में देरी)।\n\n"
            "प्रश्न: क्या RBSK इलाज मुफ्त है?\n"
            "उत्तर: हां। जांच, रेफरल और इलाज सब सरकारी अस्पतालों में मुफ्त। जन्मजात दोषों की मुफ्त सर्जरी भी।\n\n"
            "प्रश्न: जांच कहां होती है?\n"
            "उत्तर: सरकारी स्कूलों और आंगनवाड़ी केंद्रों में। RBSK मोबाइल स्वास्थ्य दल नियमित रूप से आते हैं।\n\n"
            "प्रश्न: उम्र सीमा क्या है?\n"
            "उत्तर: जन्म से 18 वर्ष तक।\n\n"
            "प्रश्न: क्या बच्चे का पंजीकरण कराना होता है?\n"
            "उत्तर: नहीं। RBSK दल स्कूलों और आंगनवाड़ियों में खुद आते हैं। इलाज के लिए नजदीकी CHC या जिला अस्पताल जाएं।"
        ),
    },
    # ── Saubhagya FAQs ────────────────────────────────────────────────────
    {
        "scheme_id": "pm-saubhagya",
        "section_id": "faqs",
        "category": "housing",
        "name_en": "Saubhagya Scheme FAQs",
        "name_hi": "सौभाग्य योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Saubhagya:\n\n"
            "Q: Is the electricity connection free?\n"
            "A: Yes, free for BPL households. APL households pay Rs 500 in 10 monthly installments of Rs 50.\n\n"
            "Q: Do I get a meter?\n"
            "A: Yes. The connection includes a meter, single-point wiring, and LED bulb.\n\n"
            "Q: Can remote areas get connection?\n"
            "A: Yes. In very remote areas where grid extension is not feasible, solar-powered off-grid solutions (200Wp solar panel with battery, LED lights, and fan) are provided.\n\n"
            "Q: How to apply?\n"
            "A: Contact your DISCOM (electricity company) or gram panchayat. Carry Aadhaar and BPL card. DISCOM field staff also identify and connect eligible households.\n\n"
            "Q: I have a connection but no electricity supply. What to do?\n"
            "A: Saubhagya is for connection only. For power supply issues, contact your DISCOM helpline or register complaint at your electricity company's portal.\n\n"
            "Q: Where to complain?\n"
            "A: Call 1912 (electricity helpline) or contact your local DISCOM office."
        ),
        "text_hi": (
            "सौभाग्य योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: क्या बिजली कनेक्शन मुफ्त है?\n"
            "उत्तर: BPL परिवारों के लिए मुफ्त। APL को 50 रुपये की 10 किस्तों में 500 रुपये देने होते हैं।\n\n"
            "प्रश्न: क्या मीटर मिलता है?\n"
            "उत्तर: हां। कनेक्शन में मीटर, सिंगल-पॉइंट वायरिंग और LED बल्ब शामिल।\n\n"
            "प्रश्न: दूरदराज क्षेत्रों में कनेक्शन?\n"
            "उत्तर: हां। जहां ग्रिड पहुंचाना संभव नहीं, वहां सोलर ऑफ-ग्रिड समाधान (200Wp सोलर पैनल, बैटरी, LED, पंखा) दिए जाते हैं।\n\n"
            "प्रश्न: आवेदन कैसे करें?\n"
            "उत्तर: DISCOM (बिजली कंपनी) या ग्राम पंचायत से संपर्क करें। आधार और BPL कार्ड लें।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: 1912 (बिजली हेल्पलाइन) पर कॉल करें या स्थानीय DISCOM कार्यालय से संपर्क करें।"
        ),
    },
    # ── Swachh Bharat Gramin FAQs ─────────────────────────────────────────
    {
        "scheme_id": "swachh-bharat-gramin",
        "section_id": "faqs",
        "category": "housing",
        "name_en": "Swachh Bharat Mission (Gramin) FAQs",
        "name_hi": "स्वच्छ भारत मिशन (ग्रामीण) अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about Swachh Bharat Mission Gramin:\n\n"
            "Q: How much money do I get for building a toilet?\n"
            "A: Rs 12,000 government incentive for building a household toilet (Rs 15,000 in some states). This is for construction including superstructure and water storage.\n\n"
            "Q: When do I get the money?\n"
            "A: The incentive is given after the toilet is built and verified by a government official. Money is transferred to your bank account.\n\n"
            "Q: Can I build any type of toilet?\n"
            "A: The toilet must have a proper substructure (twin pit, septic tank, or bio-digester), water supply, and superstructure (walls, roof, door).\n\n"
            "Q: Whose name should the toilet be in?\n"
            "A: The woman head of the household gets priority. The toilet is listed in the woman's name whenever possible.\n\n"
            "Q: How to apply?\n"
            "A: Apply at gram panchayat or Block Development Office. Carry Aadhaar, BPL card. In some states, apply online at sbm.gov.in.\n\n"
            "Q: What is ODF Plus?\n"
            "A: In Phase 2 (ODF Plus), besides maintaining toilet use, villages also get support for greywater treatment, solid waste management, and fecal sludge management.\n\n"
            "Q: Where to complain if not getting the scheme?\n"
            "A: Call 1969 (Swachh Bharat helpline), or contact Block Development Officer, or file online at swachhbharatmission.gov.in."
        ),
        "text_hi": (
            "स्वच्छ भारत मिशन (ग्रामीण) के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: शौचालय बनाने के लिए कितना पैसा मिलता है?\n"
            "उत्तर: 12,000 रुपये सरकारी प्रोत्साहन (कुछ राज्यों में 15,000)। इसमें निर्माण, दीवारें, छत और जल भंडारण शामिल।\n\n"
            "प्रश्न: पैसा कब मिलता है?\n"
            "उत्तर: शौचालय बनने और सरकारी अधिकारी द्वारा सत्यापन के बाद। बैंक खाते में ट्रांसफर।\n\n"
            "प्रश्न: कोई भी शौचालय बना सकते हैं?\n"
            "उत्तर: शौचालय में उचित गड्ढा (ट्विन पिट, सेप्टिक टैंक), पानी की व्यवस्था, और दीवारें-छत-दरवाजा होना चाहिए।\n\n"
            "प्रश्न: आवेदन कैसे करें?\n"
            "उत्तर: ग्राम पंचायत या खंड विकास कार्यालय में। आधार, BPL कार्ड लें। कुछ राज्यों में sbm.gov.in पर ऑनलाइन।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: 1969 (स्वच्छ भारत हेल्पलाइन), खंड विकास अधिकारी, या swachhbharatmission.gov.in पर ऑनलाइन।"
        ),
    },
    # ── PM Shram Yogi Mandhan FAQs ────────────────────────────────────────
    {
        "scheme_id": "pm-shram-yogi-mandhan",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM Shram Yogi Mandhan Yojana FAQs",
        "name_hi": "पीएम श्रम योगी मानधन योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Shram Yogi Mandhan:\n\n"
            "Q: How much pension will I get?\n"
            "A: Rs 3,000 per month guaranteed pension after age 60.\n\n"
            "Q: How much do I need to contribute?\n"
            "A: Rs 55 to Rs 200 per month depending on your age when you join. Government matches your contribution equally.\n\n"
            "Q: Who is eligible?\n"
            "A: Unorganised workers aged 18-40 with monthly income up to Rs 15,000. Includes domestic workers, street vendors, construction workers, rickshaw pullers, auto drivers, washermen, cobblers etc.\n\n"
            "Q: Who is NOT eligible?\n"
            "A: EPFO/ESIC/NPS members, income tax payers, and organised sector employees.\n\n"
            "Q: What happens if I die before 60?\n"
            "A: Spouse can continue contributing and get the pension at 60. Or spouse gets 50% of accumulated pension as family pension.\n\n"
            "Q: Can I exit before 60?\n"
            "A: Yes. Before 60: you get back your contribution plus bank savings account interest. Government's contribution is not returned.\n\n"
            "Q: How to register?\n"
            "A: Visit nearest CSC centre with Aadhaar and savings bank account. The VLE (Village Level Entrepreneur) will register you online.\n\n"
            "Q: How to check my PM-SYM account?\n"
            "A: Visit maandhan.in or call 1800-267-6888. CSC centres can also check account details."
        ),
        "text_hi": (
            "पीएम श्रम योगी मानधन के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: कितनी पेंशन मिलेगी?\n"
            "उत्तर: 60 साल बाद हर महीने 3,000 रुपये गारंटीशुदा पेंशन।\n\n"
            "प्रश्न: कितना योगदान देना होता है?\n"
            "उत्तर: शामिल होने की उम्र के अनुसार 55 से 200 रुपये मासिक। सरकार भी उतना ही योगदान देती है।\n\n"
            "प्रश्न: कौन पात्र है?\n"
            "उत्तर: 18-40 वर्ष के असंगठित कामगार, 15,000 रुपये तक मासिक आय। घरेलू कामगार, फेरीवाले, निर्माण श्रमिक, रिक्शा चालक, ऑटो ड्राइवर, धोबी, मोची आदि।\n\n"
            "प्रश्न: कौन पात्र नहीं?\n"
            "उत्तर: EPFO/ESIC/NPS सदस्य, आयकरदाता, संगठित क्षेत्र के कर्मचारी।\n\n"
            "प्रश्न: 60 से पहले मृत्यु हो जाए तो?\n"
            "उत्तर: पति/पत्नी योगदान जारी रखकर 60 पर पेंशन ले सकते हैं। या जमा पेंशन का 50% पारिवारिक पेंशन मिलती है।\n\n"
            "प्रश्न: पंजीकरण कैसे करें?\n"
            "उत्तर: नजदीकी CSC केंद्र में आधार और बचत खाता लेकर जाएं। VLE ऑनलाइन पंजीकरण करेगा।\n\n"
            "प्रश्न: खाता कैसे जांचें?\n"
            "उत्तर: maandhan.in पर या 1800-267-6888 पर कॉल करें।"
        ),
    },
    # ── PM Vishwakarma FAQs ───────────────────────────────────────────────
    {
        "scheme_id": "pm-vishwakarma",
        "section_id": "faqs",
        "category": "finance",
        "name_en": "PM Vishwakarma Yojana FAQs",
        "name_hi": "पीएम विश्वकर्मा योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Vishwakarma Yojana:\n\n"
            "Q: Which 18 trades are covered?\n"
            "A: Carpenter, boat maker, armourer, blacksmith, hammer and toolkit maker, locksmith, goldsmith, potter, sculptor, cobbler, mason, basket/mat maker, doll/toy maker, barber, garland maker, washerman, tailor, and fishing net maker.\n\n"
            "Q: What do I get under PM Vishwakarma?\n"
            "A: (1) PM Vishwakarma certificate and ID card, (2) 5-7 days skill training + Rs 500/day stipend, (3) Up to Rs 15,000 toolkit grant, (4) Rs 1 lakh first loan at 5% interest, then Rs 2 lakh second loan, (5) Rs 1 per transaction digital payment incentive (max Rs 100/month), (6) Marketing support.\n\n"
            "Q: What is the loan interest rate?\n"
            "A: 5% per annum. Government pays the difference as interest subvention. This is much lower than regular bank rates.\n\n"
            "Q: How to register?\n"
            "A: Step 1: Register at pmvishwakarma.gov.in with Aadhaar and mobile. Step 2: Gram Panchayat/ULB verifies your trade. Step 3: Apply for training, toolkit, and loan.\n\n"
            "Q: My trade is not in the list. Can I apply?\n"
            "A: No. Only the 18 notified trades are eligible. More trades may be added in future.\n\n"
            "Q: Is there an age limit?\n"
            "A: You must be 18+ years. No upper age limit. Must not be a government/PSU employee.\n\n"
            "Q: Can family members also apply?\n"
            "A: Only one person per family (husband-wife-minor children) can get PM Vishwakarma benefits."
        ),
        "text_hi": (
            "पीएम विश्वकर्मा योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: कौन से 18 व्यापार शामिल हैं?\n"
            "उत्तर: बढ़ई, नाव बनाने वाला, कवचकार, लोहार, हथौड़ा/औज़ार बनाने वाला, ताला बनाने वाला, सुनार, कुम्हार, मूर्तिकार, मोची, राजमिस्त्री, टोकरी/चटाई बनाने वाला, गुड़िया/खिलौना बनाने वाला, नाई, माला बनाने वाला, धोबी, दर्जी, मछली पकड़ने का जाल बनाने वाला।\n\n"
            "प्रश्न: क्या मिलता है?\n"
            "उत्तर: (1) विश्वकर्मा प्रमाणपत्र और ID कार्ड, (2) 5-7 दिन प्रशिक्षण + 500/दिन भत्ता, (3) 15,000 तक औज़ार अनुदान, (4) पहला लोन 1 लाख 5% ब्याज पर फिर 2 लाख, (5) डिजिटल भुगतान प्रोत्साहन 1 रुपये/लेनदेन (अधिकतम 100/माह), (6) मार्केटिंग सहायता।\n\n"
            "प्रश्न: लोन ब्याज दर क्या है?\n"
            "उत्तर: 5% सालाना। बाकी ब्याज सरकार देती है। बैंक दरों से बहुत कम।\n\n"
            "प्रश्न: पंजीकरण कैसे करें?\n"
            "उत्तर: चरण 1: pmvishwakarma.gov.in पर आधार और मोबाइल से पंजीकरण। चरण 2: ग्राम पंचायत/ULB सत्यापन। चरण 3: प्रशिक्षण, औज़ार और लोन आवेदन।\n\n"
            "प्रश्न: क्या उम्र सीमा है?\n"
            "उत्तर: 18+ वर्ष। ऊपरी उम्र सीमा नहीं। सरकारी/PSU कर्मचारी नहीं होना चाहिए।\n\n"
            "प्रश्न: परिवार के कितने लोगों को लाभ मिलेगा?\n"
            "उत्तर: एक परिवार (पति-पत्नी-नाबालिग बच्चे) से केवल एक व्यक्ति।"
        ),
    },
    # ── Janani Shishu Suraksha FAQs ───────────────────────────────────────
    {
        "scheme_id": "janani-shishu-suraksha",
        "section_id": "faqs",
        "category": "health",
        "name_en": "Janani Shishu Suraksha Karyakram FAQs",
        "name_hi": "जननी शिशु सुरक्षा कार्यक्रम अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about JSSK:\n\n"
            "Q: What services are free under JSSK?\n"
            "A: For pregnant women: free delivery (normal and C-section), free medicines, free diagnostics, free blood, free diet during hospital stay, free transport (home to hospital and back). For sick newborns (up to 30 days): free treatment, medicines, diagnostics, blood, and transport.\n\n"
            "Q: Does JSSK cover private hospitals?\n"
            "A: No. JSSK covers only government health facilities - PHC, CHC, district hospital, and medical college hospitals.\n\n"
            "Q: Is there any income or BPL condition?\n"
            "A: No. JSSK is for ALL pregnant women delivering in government hospitals, regardless of income or BPL status.\n\n"
            "Q: What if the hospital charges money?\n"
            "A: This is a violation of JSSK. Complain to the hospital superintendent, Chief Medical Officer, or call 1800-180-1104.\n\n"
            "Q: Does JSSK cover cesarean (C-section) delivery?\n"
            "A: Yes. Cesarean section is fully covered and free under JSSK.\n\n"
            "Q: How to get free transport under JSSK?\n"
            "A: Contact your ASHA worker or call 102 (ambulance service). Free transport is provided from home to hospital, between hospitals (referral), and hospital back to home.\n\n"
            "Q: For how long is the newborn covered?\n"
            "A: Sick newborns are covered for free treatment up to 30 days after birth."
        ),
        "text_hi": (
            "जननी शिशु सुरक्षा कार्यक्रम के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: JSSK में क्या-क्या मुफ्त है?\n"
            "उत्तर: गर्भवती महिलाओं के लिए: मुफ्त प्रसव (नॉर्मल और सी-सेक्शन), दवाइयां, जांच, रक्त, भोजन, परिवहन (घर से अस्पताल और वापस)। 30 दिन तक के बीमार नवजात: मुफ्त इलाज, दवाइयां, जांच, रक्त, परिवहन।\n\n"
            "प्रश्न: क्या JSSK प्राइवेट अस्पतालों में लागू है?\n"
            "उत्तर: नहीं। केवल सरकारी स्वास्थ्य केंद्र - PHC, CHC, जिला अस्पताल, मेडिकल कॉलेज।\n\n"
            "प्रश्न: क्या आय या BPL शर्त है?\n"
            "उत्तर: नहीं। सरकारी अस्पताल में प्रसव कराने वाली सभी गर्भवती महिलाओं के लिए।\n\n"
            "प्रश्न: अस्पताल पैसे मांगे तो?\n"
            "उत्तर: यह JSSK का उल्लंघन है। अस्पताल अधीक्षक, मुख्य चिकित्सा अधिकारी से शिकायत करें या 1800-180-1104 पर कॉल करें।\n\n"
            "प्रश्न: क्या सी-सेक्शन कवर है?\n"
            "उत्तर: हां। सी-सेक्शन JSSK में पूरी तरह मुफ्त है।\n\n"
            "प्रश्न: मुफ्त परिवहन कैसे मिले?\n"
            "उत्तर: आशा कार्यकर्ता से संपर्क करें या 102 (एंबुलेंस) पर कॉल करें। घर से अस्पताल, रेफरल और वापसी - सब मुफ्त।\n\n"
            "प्रश्न: नवजात कितने दिन तक कवर है?\n"
            "उत्तर: बीमार नवजात जन्म के 30 दिन तक मुफ्त इलाज के पात्र हैं।"
        ),
    },
    # ── PM Krishi Sinchai Yojana FAQs ─────────────────────────────────────
    {
        "scheme_id": "pm-krishi-sinchai",
        "section_id": "faqs",
        "category": "agriculture",
        "name_en": "PM Krishi Sinchai Yojana FAQs",
        "name_hi": "पीएम कृषि सिंचाई योजना अक्सर पूछे जाने वाले प्रश्न",
        "text_en": (
            "Frequently Asked Questions about PM Krishi Sinchai Yojana:\n\n"
            "Q: How much subsidy do I get on micro-irrigation?\n"
            "A: Small and marginal farmers: 55% subsidy. Other farmers: 45% subsidy on drip and sprinkler irrigation equipment.\n\n"
            "Q: Which irrigation systems are covered?\n"
            "A: Drip irrigation, sprinkler systems, rain guns, micro-sprinklers, and other micro-irrigation equipment.\n\n"
            "Q: Can I get subsidy on a borewell or tubewell?\n"
            "A: Some states provide subsidy on borewells/tubewells under the PMKSY Har Khet Ko Pani component. Check with your state Agriculture Department.\n\n"
            "Q: How to apply?\n"
            "A: Contact your District Agriculture/Horticulture Department. Some states have online portals. Carry land documents, Aadhaar, and bank details.\n\n"
            "Q: Can tenant farmers apply?\n"
            "A: Yes. Farmers with leased/rented land can also apply with proper lease agreement documents.\n\n"
            "Q: Is there a minimum land requirement?\n"
            "A: No fixed minimum. Even small plots can get micro-irrigation subsidy. Priority for small and marginal farmers (less than 2 hectares).\n\n"
            "Q: How long does subsidy take to arrive?\n"
            "A: After installation and verification, subsidy is credited to bank account within 1-3 months depending on the state.\n\n"
            "Q: Where to complain?\n"
            "A: Contact your District Agriculture Officer or call 1800-180-1551."
        ),
        "text_hi": (
            "पीएम कृषि सिंचाई योजना के बारे में अक्सर पूछे जाने वाले प्रश्न:\n\n"
            "प्रश्न: माइक्रो-सिंचाई पर कितनी सब्सिडी मिलती है?\n"
            "उत्तर: छोटे और सीमांत किसान: 55% सब्सिडी। अन्य किसान: 45% सब्सिडी - ड्रिप और स्प्रिंकलर सिंचाई उपकरणों पर।\n\n"
            "प्रश्न: कौन सी सिंचाई प्रणालियां कवर हैं?\n"
            "उत्तर: ड्रिप सिंचाई, स्प्रिंकलर, रेन गन, माइक्रो-स्प्रिंकलर और अन्य सूक्ष्म सिंचाई उपकरण।\n\n"
            "प्रश्न: क्या बोरवेल/ट्यूबवेल पर सब्सिडी मिलती है?\n"
            "उत्तर: कुछ राज्य PMKSY हर खेत को पानी घटक के तहत बोरवेल/ट्यूबवेल पर सब्सिडी देते हैं। राज्य कृषि विभाग से जांचें।\n\n"
            "प्रश्न: आवेदन कैसे करें?\n"
            "उत्तर: जिला कृषि/उद्यानिकी विभाग से संपर्क करें। कुछ राज्यों में ऑनलाइन पोर्टल। जमीन के कागजात, आधार और बैंक जानकारी लें।\n\n"
            "प्रश्न: क्या किरायेदार किसान आवेदन कर सकते हैं?\n"
            "उत्तर: हां। पट्टे/किराये की जमीन वाले किसान भी उचित पट्टा दस्तावेजों के साथ आवेदन कर सकते हैं।\n\n"
            "प्रश्न: सब्सिडी कब तक आती है?\n"
            "उत्तर: स्थापना और सत्यापन के बाद 1-3 महीने में बैंक खाते में।\n\n"
            "प्रश्न: शिकायत कहां करें?\n"
            "उत्तर: जिला कृषि अधिकारी से या 1800-180-1551 पर कॉल करें।"
        ),
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
    all_items = SCHEMES + EXTRA_SECTIONS
    for item in all_items:
        # Save to knowledge table
        knowledge_table.put_item(Item=item)
        print(f"  ✓ Knowledge: {item['scheme_id']} ({item['section_id']})")

        # Generate embeddings for English and Hindi text, save to vectors table
        for lang in ["en", "hi"]:
            text_key = f"text_{lang}"
            text = item.get(text_key, "")
            if not text:
                continue

            print(f"    Generating embedding for {item['scheme_id']}#{item['section_id']} ({lang})...")
            embedding = [Decimal(str(v)) for v in get_embedding(text)]

            vectors_table.put_item(Item={
                "embedding_id": f"{item['scheme_id']}#{item['section_id']}#{lang}",
                "scheme_id": item["scheme_id"],
                "section_id": item["section_id"],
                "language": lang,
                "text": text,
                f"text_{lang}": text,
                "embedding": embedding
            })
            print(f"    ✓ Vector stored: {item['scheme_id']}#{item['section_id']} ({lang})")

    print(f"\nDone! Knowledge base seeded with {len(SCHEMES)} scheme overviews and {len(EXTRA_SECTIONS)} FAQ sections ({len(SCHEMES) + len(EXTRA_SECTIONS)} total items).")


if __name__ == "__main__":
    seed()
