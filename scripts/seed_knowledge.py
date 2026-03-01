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
        "text_mr": "पीएम किसान योजनेत शेतकरी कुटुंबांना दरवर्षी 6000 रुपये थेट मिळतात. हे पैसे 2000-2000 रुपयांच्या 3 हप्त्यांमध्ये येतात. ज्या शेतकऱ्याकडे स्वतःची शेतजमीन आहे, तो अर्ज करू शकतो.",
        "text_ta": "பிஎம் கிசான் திட்டம் விவசாயக் குடும்பங்களுக்கு ஆண்டுக்கு 6000 ரூபாய் நேரடியாகக் கொடுக்கிறது. இந்தப் பணம் 2000 ரூபாய் வீதம் 3 தவணைகளில் வருகிறது. சொந்தமாக விவசாய நிலம் வைத்திருக்கும் எந்த விவசாயியும் விண்ணப்பிக்கலாம்.",
        "eligibility_mr": "ज्या शेतकरी कुटुंबांकडे शेतीयोग्य जमीन आहे. आयकर भरणारे, सरकारी कर्मचारी आणि व्यावसायिकांना मिळणार नाही.",
        "eligibility_ta": "விவசாய நிலம் வைத்திருக்கும் விவசாயக் குடும்பங்கள். வருமான வரி செலுத்துபவர்கள், அரசு ஊழியர்கள் அல்லது தொழில் வல்லுநர்களுக்குக் கிடைக்காது.",
        "how_to_apply_mr": "जवळच्या CSC केंद्रात जा किंवा pmkisan.gov.in वर आधार कार्ड, बँक पासबुक आणि जमिनीचे कागदपत्रे घेऊन अर्ज करा.",
        "how_to_apply_ta": "அருகிலுள்ள CSC மையத்திற்குச் செல்லுங்கள் அல்லது pmkisan.gov.in-ல் ஆதார் கார்டு, வங்கி பாஸ்புக் மற்றும் நில ஆவணங்களுடன் விண்ணப்பியுங்கள்.",
        "documents_mr": "आधार कार्ड, बँक खाते पासबुक (आधारशी लिंक), जमिनीचे कागदपत्रे (खतौनी/खसरा/जमीन मालकी हक्क), आधारशी जोडलेला मोबाइल नंबर.",
        "documents_ta": "ஆதார் கார்டு, வங்கிக் கணக்கு பாஸ்புக் (ஆதாருடன் இணைக்கப்பட்டது), நில உரிமை ஆவணங்கள் (கததோனி/கஸ்ரா/நில பட்டா), ஆதாருடன் பதிவு செய்யப்பட்ட மொபைல் எண்.",
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
        "text_mr": "आयुष्मान भारत योजना गरीब कुटुंबांना दरवर्षी 5 लाख रुपयांपर्यंत मोफत आरोग्य विमा देते. सरकारी आणि सूचीबद्ध खाजगी रुग्णालयांमध्ये मोफत उपचार मिळतो.",
        "text_ta": "ஆயுஷ்மான் பாரத் திட்டம் ஏழைக் குடும்பங்களுக்கு ஆண்டுக்கு 5 லட்சம் ரூபாய் வரை இலவச மருத்துவக் காப்பீடு கொடுக்கிறது. அரசு மற்றும் பட்டியலிடப்பட்ட தனியார் மருத்துவமனைகளில் இலவச சிகிச்சை பெறலாம்.",
        "eligibility_mr": "SECC 2011 यादीतील कुटुंबे. रोजंदारी मजूर, बांधकाम कामगार, घरकामगार यांचा समावेश. mera.pmjay.gov.in वर पात्रता तपासा.",
        "eligibility_ta": "SECC 2011 பட்டியலில் உள்ள குடும்பங்கள். தினக்கூலி தொழிலாளர்கள், கட்டுமானத் தொழிலாளர்கள், வீட்டு வேலை செய்பவர்கள் உள்ளிட்டோர். mera.pmjay.gov.in-ல் தகுதியைச் சரிபாருங்கள்.",
        "how_to_apply_mr": "जवळच्या आयुष्मान भारत सूचीबद्ध रुग्णालयात किंवा CSC मध्ये आधार घेऊन जा. यादीत आधीच असाल तर वेगळ्या नोंदणीची गरज नाही.",
        "how_to_apply_ta": "அருகிலுள்ள ஆயுஷ்மான் பாரத் பட்டியலிடப்பட்ட மருத்துவமனை அல்லது CSC-க்கு ஆதாருடன் செல்லுங்கள். ஏற்கனவே பட்டியலில் இருந்தால் தனியாகப் பதிவு செய்ய வேண்டாம்.",
        "documents_mr": "आधार कार्ड, रेशन कार्ड, SECC/RSBY कार्ड (असल्यास), कोणतेही सरकारी ओळखपत्र. आयुष्मान कार्ड रुग्णालय किंवा CSC मध्ये बनते.",
        "documents_ta": "ஆதார் கார்டு, ரேஷன் கார்டு, SECC/RSBY கார்டு (இருந்தால்), ஏதாவது அரசு அடையாள அட்டை. ஆயுஷ்மான் கார்டு மருத்துவமனை அல்லது CSC-ல் உருவாக்கப்படும்.",
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
        "text_mr": "मनरेगा ग्रामीण कुटुंबांना वर्षात 100 दिवस कामाची हमी देते. राज्यानुसार दररोज 200-300 रुपये मजुरी मिळते. ग्रामीण घरातील कोणताही प्रौढ व्यक्ती अर्ज करू शकतो.",
        "text_ta": "மகாத்மா காந்தி தேசிய ஊரக வேலை உறுதித் திட்டம் கிராமப்புறக் குடும்பங்களுக்கு ஆண்டுக்கு 100 நாள் வேலை உத்தரவாதம் அளிக்கிறது. மாநிலத்தைப் பொறுத்து தினசரி ஊதியம் 200-300 ரூபாய். கிராமப்புறக் குடும்பத்தில் உள்ள எந்தப் பெரியவரும் விண்ணப்பிக்கலாம்.",
        "eligibility_mr": "ग्रामीण घरातील कोणताही प्रौढ सदस्य जो अकुशल शारीरिक काम करण्यास तयार आहे. स्थानिक ग्रामपंचायत कार्यालयात अर्ज करा.",
        "eligibility_ta": "கிராமப்புறக் குடும்பத்தில் உள்ள எந்தவொரு பெரியவரும் உடலுழைப்பு வேலை செய்யத் தயாராக இருந்தால் தகுதி உண்டு. உள்ளூர் கிராம ஊராட்சி அலுவலகத்தில் விண்ணப்பியுங்கள்.",
        "how_to_apply_mr": "ग्रामपंचायत कार्यालयात आधार आणि बँक खाते माहिती घेऊन जा. 15 दिवसांत जॉब कार्ड मिळेल.",
        "how_to_apply_ta": "கிராம ஊராட்சி அலுவலகத்திற்கு ஆதார் மற்றும் வங்கிக் கணக்கு விவரங்களுடன் செல்லுங்கள். 15 நாட்களில் வேலை அட்டை கிடைக்கும்.",
        "documents_mr": "आधार कार्ड, पासपोर्ट साईज फोटो, बँक खाते माहिती, ग्रामीण भागात राहत असल्याचा पुरावा. उत्पन्नाचा दाखला लागत नाही.",
        "documents_ta": "ஆதார் கார்டு, பாஸ்போர்ட் அளவு புகைப்படங்கள், வங்கிக் கணக்கு விவரங்கள், கிராமப்புறத்தில் வசிப்பதற்கான சான்று. வருமானச் சான்று தேவையில்லை.",
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
        "text_mr": "पीएम आवास योजना गरीब कुटुंबांना घर बांधण्यासाठी किंवा सुधारण्यासाठी पैसे देते. ग्रामीण कुटुंबांना 1.2 लाख रुपयांपर्यंत मिळू शकतात आणि शहरी कुटुंबांना होम लोन सब्सिडी मिळते.",
        "text_ta": "பிஎம் ஆவாஸ் யோஜனா ஏழைக் குடும்பங்களுக்கு வீடு கட்ட அல்லது மேம்படுத்த பணம் கொடுக்கிறது. கிராமப்புறக் குடும்பங்களுக்கு 1.2 லட்சம் ரூபாய் வரை கிடைக்கும், நகர்ப்புறக் குடும்பங்களுக்கு வீட்டுக் கடன் மானியம் கிடைக்கும்.",
        "eligibility_mr": "ज्या कुटुंबांकडे पक्के घर नाही, EWS/LIG उत्पन्न गट. भारतात कुठेही पक्के घर असलेल्यांना मिळणार नाही.",
        "eligibility_ta": "பக்கா வீடு இல்லாத குடும்பங்கள், EWS/LIG வருமானப் பிரிவு. இந்தியாவில் எங்காவது ஏற்கனவே பக்கா வீடு உள்ள குடும்பங்களுக்குக் கிடைக்காது.",
        "how_to_apply_mr": "ग्रामपंचायत (ग्रामीण) किंवा शहरी स्थानिक स्वराज्य संस्थेत आधार, उत्पन्नाचा दाखला आणि बँक माहिती घेऊन अर्ज करा.",
        "how_to_apply_ta": "கிராம ஊராட்சி (கிராமப்புறம்) அல்லது நகர்ப்புற உள்ளாட்சி அலுவலகத்தில் ஆதார், வருமானச் சான்றிதழ் மற்றும் வங்கி விவரங்களுடன் விண்ணப்பியுங்கள்.",
        "documents_mr": "आधार कार्ड, उत्पन्नाचा दाखला, बँक खाते पासबुक, जमिनीचे कागदपत्रे (ग्रामीणसाठी), पक्के घर नसल्याचा दाखला, जातीचा दाखला (SC/ST साठी), पासपोर्ट साईज फोटो.",
        "documents_ta": "ஆதார் கார்டு, வருமானச் சான்றிதழ், வங்கிக் கணக்கு பாஸ்புக், நில ஆவணங்கள் (கிராமப்புறத்திற்கு), பக்கா வீடு இல்லை என்ற சான்றிதழ், சாதிச் சான்றிதழ் (SC/ST-க்கு), பாஸ்போர்ட் அளவு புகைப்படங்கள்.",
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
        "text_mr": "सुकन्या समृद्धी ही मुलींसाठी बचत योजना आहे. पैसे जमा केल्यावर चांगले व्याज मिळते. 18 वर्षांनंतर हे पैसे तिच्या शिक्षणासाठी किंवा लग्नासाठी वापरता येतात.",
        "text_ta": "சுகன்யா சம்ரிதி பெண் குழந்தைகளுக்கான சேமிப்புத் திட்டம். பணம் சேமித்தால் நல்ல வட்டி கிடைக்கும். 18 வயதுக்குப் பிறகு இந்தப் பணம் அவளின் படிப்பு அல்லது திருமணத்திற்குப் பயன்படும்.",
        "eligibility_mr": "10 वर्षांपेक्षा कमी वयाची कोणतीही मुलगी. पालक पोस्ट ऑफिस किंवा बँकमध्ये खाते उघडू शकतात.",
        "eligibility_ta": "10 வயதுக்குக் கீழ் உள்ள எந்தப் பெண் குழந்தையும். பெற்றோர் அல்லது பாதுகாவலர் தபால் நிலையம் அல்லது வங்கியில் கணக்கு தொடங்கலாம்.",
        "how_to_apply_mr": "जवळच्या पोस्ट ऑफिस किंवा बँकेत मुलीचा जन्म दाखला, पालकांचे आधार आणि पत्त्याचा पुरावा घेऊन जा. किमान जमा 250 रुपये.",
        "how_to_apply_ta": "அருகிலுள்ள தபால் நிலையம் அல்லது வங்கியில் பெண் குழந்தையின் பிறப்புச் சான்றிதழ், பெற்றோர் ஆதார் மற்றும் முகவரிச் சான்றுடன் செல்லுங்கள். குறைந்தபட்ச வைப்புத்தொகை 250 ரூபாய்.",
        "documents_mr": "मुलीचा जन्म दाखला, पालक/पालकांचे आधार कार्ड, पत्त्याचा पुरावा, पालक आणि मुलीचे पासपोर्ट साईज फोटो, किमान 250 रुपये जमा.",
        "documents_ta": "பெண் குழந்தையின் பிறப்புச் சான்றிதழ், பெற்றோர்/பாதுகாவலரின் ஆதார் கார்டு, முகவரிச் சான்று, பெற்றோர் மற்றும் குழந்தையின் பாஸ்போர்ட் அளவு புகைப்படங்கள், குறைந்தபட்சம் 250 ரூபாய் வைப்புத்தொகை.",
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
        "text_mr": "पीएम मुद्रा योजना छोट्या व्यापाऱ्यांना, दुकानदारांना, कारागिरांना आणि सूक्ष्म उद्योजकांना 20 लाख रुपयांपर्यंत व्यवसाय कर्ज देते. शिशु (50,000 पर्यंत), किशोर (5 लाखपर्यंत), तरुण (10 लाखपर्यंत) आणि तरुण प्लस (20 लाखपर्यंत) असे चार प्रकार आहेत.",
        "text_ta": "பிஎம் முத்ரா திட்டம் சிறு வியாபாரிகள், கடைக்காரர்கள், கைவினைஞர்கள் மற்றும் நுண் தொழில்முனைவோருக்கு 20 லட்சம் ரூபாய் வரை தொழில் கடன் கொடுக்கிறது. சிசு (50,000 வரை), கிஷோர் (5 லட்சம் வரை), தருண் (10 லட்சம் வரை), தருண் பிளஸ் (20 லட்சம் வரை) என நான்கு வகைகள் உள்ளன.",
        "eligibility_mr": "शेती नसलेला कोणताही छोटा किंवा सूक्ष्म व्यवसाय मालक. भाजी विक्रेते, शिंपी, दुरुस्तीचे दुकान, ब्यूटी पार्लर, छोटे उत्पादक यांचा समावेश.",
        "eligibility_ta": "விவசாயம் அல்லாத எந்தவொரு சிறிய அல்லது நுண் தொழில் உரிமையாளரும். காய்கறி விற்பவர், தையல்காரர், பழுதுபார்ப்புக் கடை, அழகுநிலையம், சிறு உற்பத்தியாளர்கள் அடங்குவர்.",
        "how_to_apply_mr": "कोणत्याही बँक, NBFC, किंवा MFI शाखेत अर्ज करा किंवा udyamimitra.in वर ऑनलाइन करा. आधार, व्यवसायाचा पुरावा आणि बँक खाते माहिती घेऊन जा.",
        "how_to_apply_ta": "எந்த வங்கி, NBFC அல்லது MFI கிளையிலும் விண்ணப்பியுங்கள் அல்லது udyamimitra.in-ல் ஆன்லைனில் விண்ணப்பியுங்கள். ஆதார், தொழில் சான்று மற்றும் வங்கிக் கணக்கு விவரங்களை எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, पॅन कार्ड, व्यवसाय योजना किंवा प्रकल्प अहवाल, व्यवसायाचा पुरावा (दुकान नोंदणी, परवाना, GST), बँक खाते माहिती, पासपोर्ट साईज फोटो, पत्त्याचा पुरावा.",
        "documents_ta": "ஆதார் கார்டு, பான் கார்டு, தொழில் திட்டம் அல்லது திட்ட அறிக்கை, தொழில் சான்று (கடை பதிவு, உரிமம், GST), வங்கிக் கணக்கு விவரங்கள், பாஸ்போர்ட் அளவு புகைப்படங்கள், முகவரிச் சான்று.",
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
        "text_mr": "पीएम फसल बीमा शेतकऱ्यांना पीक विमा देते. शेतकऱ्यांना खरीप पिकांसाठी फक्त 2% प्रीमियम, रब्बी पिकांसाठी 1.5% आणि व्यावसायिक पिकांसाठी 5% भरावा लागतो. उर्वरित प्रीमियम सरकार भरते आणि पीक नुकसानीवर पूर्ण भरपाई मिळते.",
        "text_ta": "பிஎம் பசல் பீமா விவசாயிகளுக்கு பயிர் காப்பீடு கொடுக்கிறது. விவசாயிகள் கரிப் பயிர்களுக்கு 2%, ரபி பயிர்களுக்கு 1.5%, வணிகப் பயிர்களுக்கு 5% பிரீமியம் மட்டுமே செலுத்த வேண்டும். மீதி பிரீமியத்தை அரசு செலுத்துகிறது, பயிர் நஷ்டத்திற்கு முழு இழப்பீடு வழங்கப்படும்.",
        "eligibility_mr": "अधिसूचित क्षेत्रांमध्ये अधिसूचित पिके घेणारे सर्व शेतकरी, वाटेकरी आणि भाडेकरू शेतकरी यांचाही समावेश. कर्ज घेतलेले शेतकरी आपोआप नोंदणीकृत होतात.",
        "eligibility_ta": "அறிவிக்கப்பட்ட பகுதிகளில் அறிவிக்கப்பட்ட பயிர்களை விளைவிக்கும் அனைத்து விவசாயிகளும், பங்கு விவசாயிகள் மற்றும் குத்தகை விவசாயிகள் உள்ளிட்டோர். கடன் வாங்கிய விவசாயிகள் தானாகவே சேர்க்கப்படுவர்.",
        "how_to_apply_mr": "अंतिम तारखेपूर्वी जवळच्या बँक, CSC किंवा pmfby.gov.in वर ऑनलाइन अर्ज करा. जमिनीचे कागदपत्रे, आधार आणि बँक पासबुक घेऊन जा.",
        "how_to_apply_ta": "கடைசிக் கெடுவுக்கு முன் அருகிலுள்ள வங்கி, CSC அல்லது pmfby.gov.in-ல் ஆன்லைனில் விண்ணப்பியுங்கள். நில ஆவணங்கள், ஆதார் மற்றும் வங்கி பாஸ்புக் எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, बँक खाते पासबुक, जमिनीचे कागदपत्रे (खतौनी/खसरा), पटवाऱ्याकडून पेरणी प्रमाणपत्र, पीक माहिती आणि पेरणी केलेले क्षेत्र.",
        "documents_ta": "ஆதார் கார்டு, வங்கிக் கணக்கு பாஸ்புக், நில உரிமை ஆவணங்கள் (கததோனி/கஸ்ரா), பட்வாரியிடம் இருந்து விதைப்புச் சான்றிதழ், பயிர் விவரங்கள் மற்றும் விதைக்கப்பட்ட பரப்பு.",
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
        "text_mr": "अटल पेन्शन योजना असंघटित क्षेत्रातील कामगारांना 60 वर्षांनंतर दरमहा 1000 ते 5000 रुपये हमखास पेन्शन देते. तुम्ही पेन्शनची रक्कम निवडता आणि वयानुसार दरमहा छोटी रक्कम भरता.",
        "text_ta": "அடல் ஓய்வூதியத் திட்டம் அமைப்புசாரா துறை தொழிலாளர்களுக்கு 60 வயதுக்குப் பிறகு மாதம் 1000 முதல் 5000 ரூபாய் உத்தரவாதமான ஓய்வூதியம் கொடுக்கிறது. நீங்கள் ஓய்வூதியத் தொகையைத் தேர்ந்தெடுத்து வயதுக்கு ஏற்ப சிறிய மாதாந்திர பங்களிப்பு செலுத்துவீர்கள்.",
        "eligibility_mr": "18 ते 40 वर्षे वयाचे भारतीय नागरिक ज्यांच्याकडे बचत बँक खाते आणि मोबाइल नंबर आहे. ऑक्टोबर 2022 पासून आयकरदाते पात्र नाहीत.",
        "eligibility_ta": "18 முதல் 40 வயது வரையிலான இந்தியக் குடிமக்கள், சேமிப்பு வங்கிக் கணக்கு மற்றும் மொபைல் எண் வைத்திருக்க வேண்டும். அக்டோபர் 2022 முதல் வருமான வரி செலுத்துபவர்கள் தகுதியற்றவர்.",
        "how_to_apply_mr": "बँक किंवा पोस्ट ऑफिसमध्ये आधार आणि मोबाइल नंबर घेऊन APY खाते उघडा. नेट बँकिंग किंवा मोबाइल बँकिंगनेही अर्ज करता येतो.",
        "how_to_apply_ta": "வங்கி அல்லது தபால் நிலையத்தில் ஆதார் மற்றும் மொபைல் எண்ணுடன் APY கணக்கு தொடங்குங்கள். நெட் பேங்கிங் அல்லது மொபைல் பேங்கிங் மூலமாகவும் விண்ணப்பிக்கலாம்.",
        "documents_mr": "आधार कार्ड, बचत बँक खाते, बँक खात्याशी जोडलेला मोबाइल नंबर. इतर कोणत्याही कागदपत्रांची गरज नाही.",
        "documents_ta": "ஆதார் கார்டு, சேமிப்பு வங்கிக் கணக்கு, வங்கிக் கணக்குடன் இணைக்கப்பட்ட மொபைல் எண். வேறு ஆவணங்கள் தேவையில்லை.",
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
        "text_mr": "पीएम स्वनिधी फेरीवाल्यांना कार्यभांडवल कर्ज देते. पहिले कर्ज 10,000, दुसरे 20,000 आणि तिसरे 50,000 रुपये. वेळेवर फेडणाऱ्यांना पुढच्या वेळी मोठे कर्ज आणि व्याज सब्सिडी मिळते.",
        "text_ta": "பிஎம் ஸ்வநிதி தெரு வியாபாரிகளுக்கு செயல்பாட்டு மூலதன கடன் கொடுக்கிறது. முதல் கடன் 10,000, இரண்டாவது 20,000, மூன்றாவது 50,000 ரூபாய். சரியான நேரத்தில் திருப்பிச் செலுத்துபவர்களுக்கு அடுத்த முறை பெரிய கடனும் வட்டி மானியமும் கிடைக்கும்.",
        "eligibility_mr": "24 मार्च 2020 रोजी किंवा त्यापूर्वी फेरीवाला व्यवसाय करत असलेले विक्रेते ज्यांच्याकडे वेंडिंग सर्टिफिकेट किंवा शहरी स्थानिक स्वराज्य संस्थेचे शिफारस पत्र आहे.",
        "eligibility_ta": "24 மார்ச் 2020 அன்று அல்லது அதற்கு முன் தெரு வியாபாரம் செய்து வந்தவர்கள், நகர்ப்புற உள்ளாட்சி அமைப்பிடம் இருந்து விற்பனைச் சான்றிதழ் அல்லது பரிந்துரைக் கடிதம் வைத்திருப்பவர்கள்.",
        "how_to_apply_mr": "pmsvanidhi.mohua.gov.in वर ऑनलाइन किंवा PM स्वनिधी मोबाइल ॲपवरून अर्ज करा. आधी पात्रता तपासा, मग शिफारस पत्र आणि कर्जासाठी अर्ज करा.",
        "how_to_apply_ta": "pmsvanidhi.mohua.gov.in-ல் ஆன்லைனில் அல்லது PM ஸ்வநிதி மொபைல் ஆப் மூலம் விண்ணப்பியுங்கள். முதலில் தகுதியைச் சரிபாருங்கள், பிறகு பரிந்துரைக் கடிதம் மற்றும் கடனுக்கு விண்ணப்பியுங்கள்.",
        "documents_mr": "आधार कार्ड, वेंडिंग सर्टिफिकेट (CoV) किंवा शहरी निकायाचे शिफारस पत्र (LoR), बँक खाते माहिती, पासपोर्ट साईज फोटो, मोबाइल नंबर.",
        "documents_ta": "ஆதார் கார்டு, விற்பனைச் சான்றிதழ் (CoV) அல்லது நகர்ப்புற உள்ளாட்சியிடம் இருந்து பரிந்துரைக் கடிதம் (LoR), வங்கிக் கணக்கு விவரங்கள், பாஸ்போர்ட் அளவு புகைப்படம், மொபைல் எண்.",
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
        "text_mr": "बेटी बचाओ बेटी पढाओ हा मुलींना वाचवण्यासाठी आणि शिकवण्यासाठी सरकारी अभियान आहे. कन्या भ्रूणहत्या रोखणे, मुलींची शाळेत नोंदणी वाढवणे आणि त्यांच्या शिक्षण व आरोग्याला मदत करणे हे याचे उद्दिष्ट आहे.",
        "text_ta": "பெண் குழந்தைகளைக் காப்பாற்றி படிக்க வைப்பதற்கான அரசு இயக்கம் இது. பெண் சிசுக்கொலையைத் தடுப்பது, பள்ளிகளில் பெண்களின் சேர்க்கையை அதிகரிப்பது, அவர்களின் படிப்பு மற்றும் ஆரோக்கியத்தை ஆதரிப்பது ஆகியவை நோக்கங்கள்.",
        "eligibility_mr": "भारतातील सर्व मुली. कमी बाल लिंग गुणोत्तर असलेल्या जिल्ह्यांवर विशेष लक्ष. आरोग्य, शिक्षण आणि समाजकल्याण विभागांमार्फत लाभ मिळतो.",
        "eligibility_ta": "இந்தியாவில் உள்ள அனைத்துப் பெண் குழந்தைகளும். குறைந்த குழந்தை பாலின விகிதம் உள்ள மாவட்டங்களுக்கு முன்னுரிமை. சுகாதாரம், கல்வி மற்றும் சமூக நல துறைகள் மூலம் பலன்கள் கிடைக்கும்.",
        "how_to_apply_mr": "तुमच्या अंगणवाडी कार्यकर्ती, आशा कार्यकर्ती किंवा जिल्हा महिला व बालविकास कार्यालयाशी संपर्क करा. रुग्णालय नोंदणी आणि शाळा प्रवेशामार्फत लाभ मिळतो.",
        "how_to_apply_ta": "உங்கள் அங்கன்வாடி பணியாளர், ஆஷா பணியாளர் அல்லது மாவட்ட மகளிர் மற்றும் குழந்தை மேம்பாட்டு அலுவலகத்தைத் தொடர்பு கொள்ளுங்கள். மருத்துவமனைப் பதிவு மற்றும் பள்ளிச் சேர்க்கை மூலம் பலன்கள் கிடைக்கும்.",
        "documents_mr": "मुलीचा जन्म दाखला, शाळा प्रवेशाचा पुरावा, रुग्णालय नोंदणी नोंदी. वेगळा अर्ज भरण्याची गरज नाही.",
        "documents_ta": "பெண் குழந்தையின் பிறப்புச் சான்றிதழ், பள்ளிச் சேர்க்கைச் சான்று, மருத்துவமனைப் பதிவு ஆவணங்கள். தனியாக விண்ணப்ப படிவம் தேவையில்லை.",
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
        "text_mr": "जननी सुरक्षा योजना गर्भवती महिलांना सरकारी किंवा मान्यताप्राप्त रुग्णालयात प्रसूती केल्यावर रोख रक्कम देते. कमी कामगिरीच्या राज्यांमध्ये ग्रामीण मातांना 1400 आणि शहरी मातांना 1000 रुपये मिळतात. मातामृत्यू आणि बालमृत्यू कमी करणे हा उद्देश आहे.",
        "text_ta": "ஜனனி சுரக்ஷா திட்டம் அரசு அல்லது அங்கீகரிக்கப்பட்ட மருத்துவமனையில் பிரசவிக்கும் கர்ப்பிணிப் பெண்களுக்கு பணம் கொடுக்கிறது. குறைந்த செயல்திறன் மாநிலங்களில் கிராமப்புற தாய்மார்களுக்கு 1400 மற்றும் நகர்ப்புற தாய்மார்களுக்கு 1000 ரூபாய் கிடைக்கும். தாய்-சேய் இறப்பைக் குறைப்பதே நோக்கம்.",
        "eligibility_mr": "सरकारी किंवा मान्यताप्राप्त खाजगी रुग्णालयात प्रसूती करणाऱ्या सर्व गर्भवती महिला. बीपीएल कुटुंबे, SC/ST महिला आणि 19 वर्षांपेक्षा अधिक वयाच्या महिलांना प्राधान्य.",
        "eligibility_ta": "அரசு அல்லது அங்கீகரிக்கப்பட்ட தனியார் மருத்துவமனைகளில் பிரசவிக்கும் அனைத்துக் கர்ப்பிணிப் பெண்களும். BPL குடும்பங்கள், SC/ST பெண்கள் மற்றும் 19 வயதுக்கு மேற்பட்ட பெண்களுக்கு முன்னுரிமை.",
        "how_to_apply_mr": "जवळच्या PHC/सब-सेंटर किंवा सरकारी रुग्णालयात प्रसूतीपूर्व तपासणीदरम्यान नोंदणी करा. आशा कार्यकर्ती कागदपत्रे आणि पैसे ट्रान्सफरमध्ये मदत करेल.",
        "how_to_apply_ta": "அருகிலுள்ள PHC/துணை மையம் அல்லது அரசு மருத்துவமனையில் மகப்பேறுக்கு முந்தைய பரிசோதனையின் போது பதிவு செய்யுங்கள். ஆஷா ஊழியர் ஆவணங்கள் மற்றும் பண பரிமாற்றத்தில் உதவுவார்.",
        "documents_mr": "आधार कार्ड, बीपीएल कार्ड किंवा रेशन कार्ड, MCH (माता आणि बाल आरोग्य) कार्ड, आधारशी जोडलेले बँक खाते पासबुक, रुग्णालय प्रसूती पुरावा.",
        "documents_ta": "ஆதார் கார்டு, BPL கார்டு அல்லது ரேஷன் கார்டு, MCH (தாய் சேய் நலன்) கார்டு, ஆதாருடன் இணைக்கப்பட்ட வங்கிக் கணக்கு பாஸ்புக், மருத்துவமனை பிரசவ சான்று.",
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
        "text_mr": "पीएम गरीब कल्याण अन्न योजना अंत्योदय आणि प्राधान्य कुटुंबातील प्रत्येक सदस्याला दरमहा 5 किलो मोफत अन्नधान्य देते. ही योजना राष्ट्रीय अन्नसुरक्षा कायद्यात समाविष्ट झाली असून 2028 पर्यंत मोफत धान्य मिळत राहील.",
        "text_ta": "பிஎம் கரீப் கல்யாண் அன்னா திட்டம் அந்தியோதயா மற்றும் முன்னுரிமை குடும்பங்களின் ஒவ்வொரு உறுப்பினருக்கும் மாதம் 5 கிலோ இலவச உணவு தானியம் கொடுக்கிறது. இத்திட்டம் தேசிய உணவுப் பாதுகாப்புச் சட்டத்தில் இணைக்கப்பட்டு 2028 வரை இலவச தானியம் கிடைக்கும்.",
        "eligibility_mr": "राष्ट्रीय अन्नसुरक्षा कायद्यांतर्गत अंत्योदय अन्न योजना (AAY) किंवा प्राधान्य कुटुंब (PHH) रेशन कार्ड असलेली कुटुंबे.",
        "eligibility_ta": "தேசிய உணவுப் பாதுகாப்புச் சட்டத்தின் கீழ் அந்தியோதயா அன்ன யோஜனா (AAY) அல்லது முன்னுரிமை குடும்ப (PHH) ரேஷன் கார்டு வைத்திருக்கும் குடும்பங்கள்.",
        "how_to_apply_mr": "वेगळ्या अर्जाची गरज नाही. दरमहा तुमच्या रेशन दुकानातून रेशन कार्ड आणि आधार दाखवून मोफत धान्य घ्या.",
        "how_to_apply_ta": "தனியாக விண்ணப்பிக்கத் தேவையில்லை. ஒவ்வொரு மாதமும் உங்கள் நியாய விலைக் கடையில் ரேஷன் கார்டு மற்றும் ஆதார் காட்டி இலவச தானியம் பெறுங்கள்.",
        "documents_mr": "रेशन कार्ड (AAY किंवा PHH श्रेणी), रेशन दुकानावर बायोमेट्रिक पडताळणीसाठी आधार कार्ड. इतर कोणत्याही कागदपत्रांची गरज नाही.",
        "documents_ta": "ரேஷன் கார்டு (AAY அல்லது PHH பிரிவு), நியாய விலைக் கடையில் பயோமெட்ரிக் சரிபார்ப்புக்கு ஆதார் கார்டு. வேறு ஆவணங்கள் தேவையில்லை.",
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
        "text_mr": "पीएम जन धन प्रत्येक बँक खाते नसलेल्या भारतीयाला मोफत RuPay डेबिट कार्डसह शून्य शिल्लक बँक खाते देते. सोबत 2 लाख रुपये अपघात विमा, 30,000 रुपये जीवन विमा आणि चांगल्या खात्यानंतर 10,000 रुपये ओव्हरड्राफ्ट सुविधा मिळते.",
        "text_ta": "பிஎம் ஜன் தன் வங்கிக் கணக்கு இல்லாத ஒவ்வொரு இந்தியருக்கும் இலவச RuPay டெபிட் கார்டுடன் பூஜ்ஜிய இருப்பு வங்கிக் கணக்கு கொடுக்கிறது. 2 லட்சம் ரூபாய் விபத்துக் காப்பீடு, 30,000 ரூபாய் ஆயுள் காப்பீடு மற்றும் நல்ல கணக்கு வரலாற்றுக்குப் பிறகு 10,000 ரூபாய் ஓவர்டிராஃப்ட் வசதியும் கிடைக்கும்.",
        "eligibility_mr": "10 वर्षांपेक्षा अधिक वयाचा कोणताही भारतीय नागरिक ज्याचे बँक खाते नाही. आधार कार्ड किंवा कोणतेही सरकारी मान्य कागदपत्र लागते.",
        "eligibility_ta": "10 வயதுக்கு மேற்பட்ட எந்த இந்தியக் குடிமகனும் வங்கிக் கணக்கு இல்லாதவர். ஆதார் கார்டு அல்லது ஏதாவது அரசு அங்கீகரிக்கப்பட்ட ஆவணம் தேவை.",
        "how_to_apply_mr": "कोणत्याही बँक शाखेत किंवा बिझनेस कॉरस्पॉन्डंट (BC) कडे आधार घेऊन जा. शून्य शिल्लकवर खाते उघडते. किमान ठेवीची गरज नाही.",
        "how_to_apply_ta": "எந்த வங்கிக் கிளை அல்லது வணிக நிருபர் (BC) மையத்திற்கும் ஆதாருடன் செல்லுங்கள். பூஜ்ஜிய இருப்பில் கணக்கு திறக்கப்படும். குறைந்தபட்ச வைப்புத்தொகை தேவையில்லை.",
        "documents_mr": "आधार कार्ड (प्राथमिक). आधार नसल्यास: मतदार ओळखपत्र, ड्रायव्हिंग लायसन्स, पॅन कार्ड, पासपोर्ट, नरेगा जॉब कार्ड, किंवा कोणतेही सरकारी फोटो ओळखपत्र.",
        "documents_ta": "ஆதார் கார்டு (முதன்மை). ஆதார் இல்லை என்றால்: வாக்காளர் அட்டை, ஓட்டுநர் உரிமம், பான் கார்டு, பாஸ்போர்ட், நரேகா வேலை அட்டை, அல்லது ஏதாவது அரசு புகைப்பட அடையாள அட்டை.",
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
        "text_mr": "पीएम उज्ज्वला गरीब घरातील महिलांना मोफत LPG गॅस कनेक्शन देते. सरकार कनेक्शनसाठी 1600 रुपये मदत, पहिला गॅस सिलेंडर आणि चूल मोफत देते. यामुळे महिलांचे घरातील धुरापासून रक्षण होते.",
        "text_ta": "பிஎம் உஜ்வாலா ஏழைக் குடும்பங்களைச் சேர்ந்த பெண்களுக்கு இலவச LPG கேஸ் இணைப்பு கொடுக்கிறது. அரசு இணைப்புக்கு 1600 ரூபாய் உதவி, முதல் சிலிண்டர் மற்றும் அடுப்பு இலவசமாகக் கொடுக்கிறது. இது பெண்களை வீட்டுக்குள் சமையல் புகையிலிருந்து காக்கிறது.",
        "eligibility_mr": "बीपीएल घरातील, SC/ST कुटुंबातील, PMAY लाभार्थी, अंत्योदय कुटुंबातील, वन/बेट-द्वीप निवासी आणि अत्यंत मागासवर्गीय कुटुंबातील प्रौढ महिला.",
        "eligibility_ta": "BPL குடும்பங்கள், SC/ST குடும்பங்கள், PMAY பயனாளிகள், அந்தியோதயா குடும்பங்கள், காடு/தீவு வாழ் மக்கள் மற்றும் மிகவும் பிற்படுத்தப்பட்ட வகுப்பினரின் பெரிய பெண்கள்.",
        "how_to_apply_mr": "pmuy.gov.in वर ऑनलाइन अर्ज करा किंवा जवळच्या LPG वितरकाकडे आधार, BPL रेशन कार्ड आणि बँक खाते माहिती घेऊन जा.",
        "how_to_apply_ta": "pmuy.gov.in-ல் ஆன்லைனில் விண்ணப்பியுங்கள் அல்லது அருகிலுள்ள LPG விநியோகஸ்தரிடம் ஆதார், BPL ரேஷன் கார்டு மற்றும் வங்கிக் கணக்கு விவரங்களுடன் செல்லுங்கள்.",
        "documents_mr": "महिला अर्जदाराचे आधार कार्ड, BPL रेशन कार्ड, बँक खाते पासबुक, पासपोर्ट साईज फोटो, पत्त्याचा पुरावा, जातीचा दाखला (SC/ST साठी).",
        "documents_ta": "பெண் விண்ணப்பதாரரின் ஆதார் கார்டு, BPL ரேஷன் கார்டு, வங்கிக் கணக்கு பாஸ்புக், பாஸ்போர்ட் அளவு புகைப்படம், முகவரிச் சான்று, சாதிச் சான்றிதழ் (SC/ST-க்கு).",
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
        "text_mr": "राष्ट्रीय शिष्यवृत्ती पोर्टल हे केंद्र आणि राज्य सरकारच्या सर्व शिष्यवृत्तींसाठी एकच व्यासपीठ आहे. SC, ST, OBC, अल्पसंख्याक आणि दिव्यांग विद्यार्थी शाळा आणि महाविद्यालयीन शिक्षणासाठी प्री-मॅट्रिक आणि पोस्ट-मॅट्रिक शिष्यवृत्तीसाठी अर्ज करू शकतात.",
        "text_ta": "தேசிய உதவித்தொகை வலைதளம் மத்திய மற்றும் மாநில அரசு உதவித்தொகைகள் அனைத்துக்கும் ஒரே தளமாகும். SC, ST, OBC, சிறுபான்மையினர் மற்றும் மாற்றுத்திறனாளி மாணவர்கள் பள்ளி மற்றும் கல்லூரிப் படிப்புக்கு முன்-மெட்ரிக் மற்றும் பின்-மெட்ரிக் உதவித்தொகைக்கு விண்ணப்பிக்கலாம்.",
        "eligibility_mr": "SC, ST, OBC, अल्पसंख्याक समुदाय आणि दिव्यांग विद्यार्थी जे शाळा किंवा महाविद्यालयात शिकत आहेत. उत्पन्न मर्यादा शिष्यवृत्तीनुसार वेगवेगळी आहे.",
        "eligibility_ta": "SC, ST, OBC, சிறுபான்மை சமூகம் மற்றும் மாற்றுத்திறனாளி மாணவர்கள் பள்ளி அல்லது கல்லூரியில் படிப்பவர்கள். வருமான வரம்பு உதவித்தொகைக்கு ஏற்ப மாறுபடும்.",
        "how_to_apply_mr": "scholarships.gov.in वर आधारने नोंदणी करा आणि One-Time Registration (OTR) नंबर बनवा. अंतिम तारखेपूर्वी शैक्षणिक आणि बँक कागदपत्रांसह अर्ज करा.",
        "how_to_apply_ta": "scholarships.gov.in-ல் ஆதாருடன் பதிவு செய்து One-Time Registration (OTR) எண் பெறுங்கள். கடைசிக் கெடுவுக்கு முன் கல்வி மற்றும் வங்கி ஆவணங்களுடன் விண்ணப்பியுங்கள்.",
        "documents_mr": "आधार कार्ड, उत्पन्नाचा दाखला, जातीचा दाखला (SC/ST/OBC/अल्पसंख्याक), दिव्यांग प्रमाणपत्र (लागू असल्यास), मागील वर्षाची गुणपत्रिका, सध्याच्या प्रवेशाचा पुरावा, बँक खाते पासबुक, पासपोर्ट साईज फोटो.",
        "documents_ta": "ஆதார் கார்டு, வருமானச் சான்றிதழ், சாதிச் சான்றிதழ் (SC/ST/OBC/சிறுபான்மை), மாற்றுத்திறனாளி சான்றிதழ் (பொருந்தினால்), முந்தைய ஆண்டு மதிப்பெண் பட்டியல், தற்போதைய சேர்க்கைச் சான்று, வங்கிக் கணக்கு பாஸ்புக், பாஸ்போர்ட் அளவு புகைப்படம்.",
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
        "text_mr": "मृदा आरोग्य कार्ड प्रत्येक शेतकऱ्याला त्याच्या मातीच्या आरोग्याचा अहवाल देते. मातीत कोणते पोषक तत्वे आहेत आणि कोणते खत वापरावे हे सांगते. दर 2 वर्षांनी कार्ड मिळते ज्यामुळे माती सुधारून चांगले पीक येते.",
        "text_ta": "மண் ஆரோக்கிய அட்டை ஒவ்வொரு விவசாயிக்கும் அவரது மண்ணின் ஆரோக்கிய அறிக்கை கொடுக்கிறது. மண்ணில் என்ன ஊட்டச்சத்துக்கள் இருக்கின்றன, என்ன உரம் பயன்படுத்த வேண்டும் என்பதைச் சொல்கிறது. 2 ஆண்டுகளுக்கு ஒருமுறை அட்டை கிடைக்கும், இதனால் மண்ணை மேம்படுத்தி நல்ல பயிர் பெறலாம்.",
        "eligibility_mr": "भारतातील सर्व शेतकरी. पूर्णपणे मोफत. कृषी विभाग आणि कृषी विज्ञान केंद्रांमार्फत उपलब्ध.",
        "eligibility_ta": "இந்தியா முழுவதும் உள்ள அனைத்து விவசாயிகளும். முற்றிலும் இலவசம். வேளாண்மைத் துறை மற்றும் கிருஷி விக்யான் கேந்திராக்கள் மூலம் கிடைக்கும்.",
        "how_to_apply_mr": "स्थानिक कृषी विभाग कार्यालय किंवा कृषी विज्ञान केंद्राशी संपर्क करा. तुमच्या शेतातून मातीचे नमुने घेऊन तपासणी केली जाईल.",
        "how_to_apply_ta": "உள்ளூர் வேளாண்மைத் துறை அலுவலகம் அல்லது கிருஷி விக்யான் கேந்திராவைத் தொடர்பு கொள்ளுங்கள். உங்கள் நிலத்திலிருந்து மண் மாதிரிகள் எடுத்துப் பரிசோதிக்கப்படும்.",
        "documents_mr": "आधार कार्ड आणि जमिनीची माहिती. औपचारिक अर्जाची गरज नाही - सरळ कृषी विभाग किंवा KVK शी संपर्क करा.",
        "documents_ta": "ஆதார் கார்டு மற்றும் நில விவரங்கள். முறையான விண்ணப்பம் தேவையில்லை - நேரடியாக வேளாண்மைத் துறை அல்லது KVK-ஐ தொடர்பு கொள்ளுங்கள்.",
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
        "text_mr": "पीएम पोषण योजना सरकारी आणि अनुदानित शाळांमध्ये इयत्ता 1 ते 8 च्या मुलांना मोफत शिजवलेले जेवण देते. प्राथमिक मुलांना 450 कॅलरी आणि उच्च प्राथमिक मुलांना 700 कॅलरी मिळते. यामुळे पोषण आणि शाळेतील उपस्थिती वाढते.",
        "text_ta": "பிஎம் போஷன் திட்டம் அரசு மற்றும் உதவி பெறும் பள்ளிகளில் 1 முதல் 8 ஆம் வகுப்பு வரை உள்ள குழந்தைகளுக்கு இலவச சமைக்கப்பட்ட உணவு கொடுக்கிறது. தொடக்கக் குழந்தைகளுக்கு 450 கலோரி, நடுநிலைக் குழந்தைகளுக்கு 700 கலோரி கிடைக்கும். இது ஊட்டச்சத்து மற்றும் பள்ளி வருகையை மேம்படுத்துகிறது.",
        "eligibility_mr": "सरकारी, सरकारी अनुदानित आणि स्थानिक स्वराज्य संस्थांच्या शाळांमध्ये इयत्ता 1 ते 8 मध्ये शिकणारी सर्व मुले. अर्जाची गरज नाही.",
        "eligibility_ta": "அரசு, அரசு உதவி பெறும் மற்றும் உள்ளாட்சி அமைப்பு பள்ளிகளில் 1 முதல் 8 ஆம் வகுப்பு வரை படிக்கும் அனைத்துக் குழந்தைகளும். விண்ணப்பம் தேவையில்லை.",
        "how_to_apply_mr": "अर्जाची गरज नाही. पात्र शाळांमध्ये आपोआप जेवण दिले जाते. माहितीसाठी शाळा मुख्याध्यापकांशी संपर्क करा.",
        "how_to_apply_ta": "விண்ணப்பம் தேவையில்லை. தகுதியான பள்ளிகளில் தானாகவே உணவு வழங்கப்படுகிறது. விவரங்களுக்கு பள்ளி தலைமை ஆசிரியரைத் தொடர்பு கொள்ளுங்கள்.",
        "documents_mr": "विद्यार्थ्यांसाठी कोणत्याही कागदपत्रांची गरज नाही. सरकारी किंवा अनुदानित शाळेत इयत्ता 1 ते 8 मध्ये प्रवेश पुरेसा आहे.",
        "documents_ta": "மாணவர்களுக்கு ஆவணங்கள் தேவையில்லை. அரசு அல்லது அரசு உதவி பெறும் பள்ளியில் 1 முதல் 8 ஆம் வகுப்பு வரை சேர்ந்திருப்பதே போதுமானது.",
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
        "text_mr": "महिला सन्मान बचत प्रमाणपत्र महिला आणि मुलींसाठी 2 वर्षांची बचत योजना आहे. 2 लाख रुपयांपर्यंत जमा केल्यास वार्षिक 7.5% व्याज मिळते. 1 वर्षानंतर आंशिक रक्कम काढता येते. पोस्ट ऑफिस आणि बँकांमध्ये उपलब्ध.",
        "text_ta": "மகிளா சம்மான் சேமிப்புச் சான்றிதழ் பெண்கள் மற்றும் சிறுமிகளுக்கான 2 ஆண்டு சேமிப்புத் திட்டம். 2 லட்சம் ரூபாய் வரை சேமித்தால் ஆண்டுக்கு 7.5% வட்டி கிடைக்கும். 1 ஆண்டுக்குப் பிறகு பகுதியாக எடுக்கலாம். தபால் நிலையங்கள் மற்றும் வங்கிகளில் கிடைக்கும்.",
        "eligibility_mr": "भारतातील कोणतीही महिला किंवा मुलगी. नाबालिग मुलीसाठी पालक/पालक खाते उघडू शकतात. एका संस्थेत एका व्यक्तीचे एक खाते.",
        "eligibility_ta": "இந்தியாவில் உள்ள எந்தப் பெண்ணும் அல்லது சிறுமியும். சிறுவயது சிறுமிக்கு பெற்றோர்/பாதுகாவலர் கணக்கு திறக்கலாம். ஒரு நிறுவனத்தில் ஒரு நபருக்கு ஒரு கணக்கு.",
        "how_to_apply_mr": "कोणत्याही पोस्ट ऑफिस किंवा अधिकृत बँकेत आधार, पॅन कार्ड आणि पासपोर्ट साईज फोटो घेऊन जा. किमान जमा 1000 रुपये.",
        "how_to_apply_ta": "எந்த தபால் நிலையம் அல்லது அங்கீகரிக்கப்பட்ட வங்கியிலும் ஆதார், பான் கார்டு மற்றும் பாஸ்போர்ட் அளவு புகைப்படத்துடன் செல்லுங்கள். குறைந்தபட்ச வைப்புத்தொகை 1000 ரூபாய்.",
        "documents_mr": "आधार कार्ड, पॅन कार्ड, पासपोर्ट साईज फोटो, पत्त्याचा पुरावा. नाबालिग मुलीसाठी: जन्म दाखला आणि पालकांची कागदपत्रे.",
        "documents_ta": "ஆதார் கார்டு, பான் கார்டு, பாஸ்போர்ட் அளவு புகைப்படம், முகவரிச் சான்று. சிறுவயது சிறுமிக்கு: பிறப்புச் சான்றிதழ் மற்றும் பெற்றோர்/பாதுகாவலர் ஆவணங்கள்.",
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
        "text_mr": "पीएम कौशल विकास योजना भारतीय तरुणांना मोफत कौशल्य प्रशिक्षण आणि प्रमाणपत्र देते. इलेक्ट्रिशियन, प्लंबर, ब्यूटीशियन, कॉम्प्युटर आणि वेल्डिंग अशा कामांमध्ये ट्रेनिंग मिळते. कोर्स पूर्ण केल्यावर नोकरी लावण्यात मदत मिळते.",
        "text_ta": "பிஎம் கௌஷல் விகாஸ் திட்டம் இந்திய இளைஞர்களுக்கு இலவச திறன் பயிற்சி மற்றும் சான்றிதழ் கொடுக்கிறது. எலக்ட்ரீஷியன், பிளம்பர், பியூட்டீஷியன், கணினி மற்றும் வெல்டிங் போன்ற வேலைகளில் பயிற்சி கிடைக்கும். பயிற்சி முடித்த பிறகு வேலை கிடைக்க உதவி செய்யப்படும்.",
        "eligibility_mr": "शाळा/महाविद्यालय सोडलेले किंवा बेरोजगार भारतीय तरुण. प्रत्येक जिल्ह्यात PMKVY प्रशिक्षण केंद्रे उपलब्ध.",
        "eligibility_ta": "பள்ளி/கல்லூரி படிப்பை நிறுத்தியவர்கள் அல்லது வேலையில்லாத இந்திய இளைஞர்கள். ஒவ்வொரு மாவட்டத்திலும் PMKVY பயிற்சி மையங்கள் உள்ளன.",
        "how_to_apply_mr": "जवळच्या PMKVY प्रशिक्षण केंद्रावर जा किंवा skillindia.gov.in वर नोंदणी करा. आधार आणि शैक्षणिक कागदपत्रे घेऊन जा.",
        "how_to_apply_ta": "அருகிலுள்ள PMKVY பயிற்சி மையத்திற்குச் செல்லுங்கள் அல்லது skillindia.gov.in-ல் பதிவு செய்யுங்கள். ஆதார் மற்றும் கல்வி ஆவணங்களை எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, शैक्षणिक प्रमाणपत्रे (असल्यास), बँक खाते माहिती, पासपोर्ट साईज फोटो, मोबाइल नंबर.",
        "documents_ta": "ஆதார் கார்டு, கல்விச் சான்றிதழ்கள் (இருந்தால்), வங்கிக் கணக்கு விவரங்கள், பாஸ்போர்ட் அளவு புகைப்படங்கள், மொபைல் எண்.",
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
        "text_mr": "पीएम सुरक्षा बीमा योजनेत फक्त वार्षिक 20 रुपयांत 2 लाख रुपयांचा अपघात विमा मिळतो. अपघातात मृत्यू किंवा पूर्ण अपंगत्वावर कुटुंबाला 2 लाख आणि आंशिक अपंगत्वावर 1 लाख रुपये मिळतात.",
        "text_ta": "பிஎம் சுரக்ஷா பீமா திட்டத்தில் ஆண்டுக்கு வெறும் 20 ரூபாயில் 2 லட்சம் ரூபாய் விபத்துக் காப்பீடு கிடைக்கும். விபத்தில் இறப்பு அல்லது முழு ஊனம் ஏற்பட்டால் குடும்பத்திற்கு 2 லட்சமும், பகுதி ஊனத்திற்கு 1 லட்சமும் வழங்கப்படும்.",
        "eligibility_mr": "18 ते 70 वर्षे वयाचे भारतीय नागरिक ज्यांच्याकडे बचत बँक खाते आहे. 20 रुपये प्रीमियम दरवर्षी खात्यातून आपोआप कापले जाते.",
        "eligibility_ta": "18 முதல் 70 வயது வரையிலான இந்தியக் குடிமக்கள், சேமிப்பு வங்கிக் கணக்கு வைத்திருக்க வேண்டும். 20 ரூபாய் பிரீமியம் ஒவ்வொரு ஆண்டும் கணக்கிலிருந்து தானாகவே கழிக்கப்படும்.",
        "how_to_apply_mr": "बँक शाखेत जा, किंवा नेट बँकिंग/मोबाइल बँकिंगने अर्ज करा. एक पानाचा फॉर्म भरा आणि ऑटो-डेबिटची संमती द्या.",
        "how_to_apply_ta": "வங்கிக் கிளைக்குச் செல்லுங்கள், அல்லது நெட் பேங்கிங்/மொபைல் பேங்கிங் மூலம் விண்ணப்பியுங்கள். ஒரு பக்க படிவம் நிரப்பி ஆட்டோ-டெபிட் ஒப்புதல் கொடுங்கள்.",
        "documents_mr": "बचत बँक खाते, आधार कार्ड. एक पानाचा नोंदणी फॉर्म सही केलेला. कोणतीही वैद्यकीय तपासणी लागत नाही.",
        "documents_ta": "சேமிப்பு வங்கிக் கணக்கு, ஆதார் கார்டு. ஒரு பக்க சேர்க்கை படிவம் கையொப்பமிடப்பட்டது. மருத்துவப் பரிசோதனை தேவையில்லை.",
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
        "text_mr": "पीएम जीवन ज्योती बीमा वार्षिक 436 रुपयांत 2 लाख रुपयांचा जीवन विमा देतो. विमाधारक व्यक्तीचा कोणत्याही कारणाने मृत्यू झाल्यास कुटुंबाला 2 लाख रुपये मिळतात. प्रीमियम बँक खात्यातून वर्षातून एकदा कापले जाते.",
        "text_ta": "பிஎம் ஜீவன் ஜோதி பீமா ஆண்டுக்கு 436 ரூபாயில் 2 லட்சம் ரூபாய் ஆயுள் காப்பீடு கொடுக்கிறது. காப்பீடு செய்தவர் எந்தக் காரணத்தாலும் இறந்தால் குடும்பத்திற்கு 2 லட்சம் ரூபாய் கிடைக்கும். பிரீமியம் வங்கிக் கணக்கிலிருந்து ஆண்டுக்கு ஒருமுறை கழிக்கப்படும்.",
        "eligibility_mr": "18 ते 55 वर्षे वयाचे भारतीय नागरिक ज्यांच्याकडे बचत बँक खाते आहे. प्रीमियम ऑटो-डेबिटची संमती आवश्यक.",
        "eligibility_ta": "18 முதல் 55 வயது வரையிலான இந்தியக் குடிமக்கள், சேமிப்பு வங்கிக் கணக்கு வைத்திருக்க வேண்டும். பிரீமியம் ஆட்டோ-டெபிட் ஒப்புதல் அவசியம்.",
        "how_to_apply_mr": "बँक शाखेत जा, किंवा नेट बँकिंग/मोबाइल बँकिंगने अर्ज करा. एक पानाचा फॉर्म आणि ऑटो-डेबिट संमती आवश्यक.",
        "how_to_apply_ta": "வங்கிக் கிளைக்குச் செல்லுங்கள், அல்லது நெட் பேங்கிங்/மொபைல் பேங்கிங் மூலம் விண்ணப்பியுங்கள். ஒரு பக்க படிவம் மற்றும் ஆட்டோ-டெபிட் ஒப்புதல் தேவை.",
        "documents_mr": "बचत बँक खाते, आधार कार्ड, ऑटो-डेबिट संमतीसहित नोंदणी फॉर्म. कोणतीही वैद्यकीय तपासणी आवश्यक नाही.",
        "documents_ta": "சேமிப்பு வங்கிக் கணக்கு, ஆதார் கார்டு, ஆட்டோ-டெபிட் ஒப்புதலுடன் சேர்க்கை படிவம். மருத்துவப் பரிசோதனை தேவையில்லை.",
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
        "text_mr": "स्टँड अप इंडिया SC/ST आणि महिला उद्योजकांना उत्पादन, सेवा किंवा व्यापारात नवीन व्यवसाय सुरू करण्यासाठी 10 लाख ते 1 कोटी रुपयांपर्यंत बँक कर्ज देते. प्रत्येक बँक शाखेतून किमान एक SC/ST आणि एक महिला कर्जदार.",
        "text_ta": "ஸ்டேண்ட் அப் இந்தியா SC/ST மற்றும் பெண் தொழில்முனைவோருக்கு உற்பத்தி, சேவை அல்லது வர்த்தகத்தில் புதிய தொழில் தொடங்க 10 லட்சம் முதல் 1 கோடி ரூபாய் வரை வங்கிக் கடன் கொடுக்கிறது. ஒவ்வொரு வங்கிக் கிளையிலிருந்தும் குறைந்தது ஒரு SC/ST மற்றும் ஒரு பெண் கடன் பெறுவார்.",
        "eligibility_mr": "SC/ST आणि/किंवा 18+ वर्षे वयाच्या महिला उद्योजक जे पहिल्यांदा उत्पादन, सेवा किंवा व्यापारात नवीन उद्यम सुरू करत आहेत.",
        "eligibility_ta": "SC/ST மற்றும்/அல்லது 18+ வயதான பெண் தொழில்முனைவோர், உற்பத்தி, சேவை அல்லது வர்த்தகத்தில் முதல்முறையாக புதிய தொழில் தொடங்குபவர்கள்.",
        "how_to_apply_mr": "standupmitra.in वर ऑनलाइन अर्ज करा किंवा कोणत्याही अनुसूचित वाणिज्य बँक शाखेत जा. आधार, प्रकल्प अहवाल आणि जात/ओळख कागदपत्रे घेऊन जा.",
        "how_to_apply_ta": "standupmitra.in-ல் ஆன்லைனில் விண்ணப்பியுங்கள் அல்லது எந்த அட்டவணை வணிக வங்கிக் கிளைக்கும் செல்லுங்கள். ஆதார், திட்ட அறிக்கை மற்றும் சாதி/அடையாள ஆவணங்களை எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, पॅन कार्ड, जातीचा दाखला (SC/ST साठी), प्रकल्प अहवाल/व्यवसाय योजना, पत्त्याचा पुरावा, बँक खाते माहिती, ओळखपत्र, पासपोर्ट साईज फोटो.",
        "documents_ta": "ஆதார் கார்டு, பான் கார்டு, சாதிச் சான்றிதழ் (SC/ST-க்கு), திட்ட அறிக்கை/தொழில் திட்டம், முகவரிச் சான்று, வங்கிக் கணக்கு விவரங்கள், அடையாளச் சான்று, பாஸ்போர்ட் அளவு புகைப்படங்கள்.",
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
        "text_mr": "पीएम मातृ वंदना योजना पहिल्या बाळासाठी गर्भवती महिलांना 3 हप्त्यांमध्ये 5000 रुपये थेट बँक खात्यात देते. दुसरे बाळ मुलगी असल्यास 6000 रुपये मिळतात. गर्भावस्थेत आरोग्य आणि पोषणासाठी मदत करते.",
        "text_ta": "பிஎம் மாத்ரு வந்தனா திட்டம் முதல் குழந்தைக்கு கர்ப்பிணிப் பெண்களுக்கு 3 தவணைகளில் 5000 ரூபாய் நேரடியாக வங்கிக் கணக்கில் கொடுக்கிறது. இரண்டாவது குழந்தை பெண் ஆக இருந்தால் 6000 ரூபாய் கிடைக்கும். கர்ப்ப காலத்தில் ஆரோக்கியம் மற்றும் ஊட்டச்சத்துக்கு உதவுகிறது.",
        "eligibility_mr": "पहिल्या जिवंत बाळासाठी गर्भवती आणि स्तनपान करणाऱ्या माता. दुसऱ्या बाळाचा लाभ फक्त मुलगी असल्यास.",
        "eligibility_ta": "முதல் உயிர்ப்பிறப்புக்கு கர்ப்பிணி மற்றும் பாலூட்டும் தாய்மார்கள். இரண்டாவது குழந்தை பலன் குழந்தை பெண்ணாக இருந்தால் மட்டுமே.",
        "how_to_apply_mr": "अंगणवाडी केंद्र किंवा मान्यताप्राप्त आरोग्य केंद्रात नोंदणी करा. आधार, बँक पासबुक आणि MCP कार्ड घेऊन जा.",
        "how_to_apply_ta": "அங்கன்வாடி மையம் அல்லது அங்கீகரிக்கப்பட்ட சுகாதார மையத்தில் பதிவு செய்யுங்கள். ஆதார், வங்கி பாஸ்புக் மற்றும் MCP கார்டு எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, आधारशी जोडलेले बँक खाते पासबुक, MCP (माता आणि बाल संरक्षण) कार्ड, गर्भावस्था नोंदणी पुरावा, रुग्णालय/ANM प्रसूती नोंद.",
        "documents_ta": "ஆதார் கார்டு, ஆதாருடன் இணைக்கப்பட்ட வங்கிக் கணக்கு பாஸ்புக், MCP (தாய் மற்றும் குழந்தை பாதுகாப்பு) கார்டு, கர்ப்பப் பதிவு சான்று, மருத்துவமனை/ANM பிரசவ ஆவணம்.",
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
        "text_mr": "राष्ट्रीय कुटुंब लाभ योजना कुटुंबातील मुख्य कमावत्या व्यक्तीच्या मृत्यूनंतर बीपीएल कुटुंबाला 20,000 रुपये एकदाच मदत देते. अर्जानंतर 4 आठवड्यांत हयात असलेल्या सदस्याला पैसे मिळतात.",
        "text_ta": "தேசிய குடும்ப நலன் திட்டம் குடும்பத்தின் முதன்மை சம்பாதிப்பவர் இறந்த பிறகு BPL குடும்பத்திற்கு 20,000 ரூபாய் ஒரு முறை உதவி கொடுக்கிறது. விண்ணப்பித்த 4 வாரங்களுக்குள் உயிருடன் இருக்கும் உறுப்பினருக்கு பணம் வழங்கப்படும்.",
        "eligibility_mr": "बीपीएल कुटुंबे ज्यांच्यातील मुख्य कमावत्या (18-60 वर्षे) व्यक्तीचा मृत्यू झाला आहे. ग्रामीण आणि शहरी दोन्ही कुटुंबे पात्र.",
        "eligibility_ta": "முதன்மை சம்பாதிப்பவர் (18-60 வயது) இறந்த BPL குடும்பங்கள். கிராமப்புற மற்றும் நகர்ப்புற இரண்டு குடும்பங்களும் தகுதி உடையவர்.",
        "how_to_apply_mr": "जिल्हा समाजकल्याण कार्यालयात किंवा NSAP पोर्टलवर अर्ज करा. मृत्यू दाखला, बीपीएल कार्ड, आधार आणि बँक माहिती घेऊन जा.",
        "how_to_apply_ta": "மாவட்ட சமூக நலன் அலுவலகத்தில் அல்லது NSAP வலைதளத்தில் விண்ணப்பியுங்கள். இறப்புச் சான்றிதழ், BPL கார்டு, ஆதார் மற்றும் வங்கி விவரங்களை எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "कमावत्या व्यक्तीचा मृत्यू दाखला, बीपीएल कार्ड, अर्जदार आणि मृत व्यक्तीचे आधार कार्ड, बँक खाते पासबुक, मृत व्यक्तीचे वय पुरावा, FIR प्रत (लागू असल्यास).",
        "documents_ta": "சம்பாதிப்பவரின் இறப்புச் சான்றிதழ், BPL கார்டு, விண்ணப்பதாரர் மற்றும் இறந்தவரின் ஆதார் கார்டு, வங்கிக் கணக்கு பாஸ்புக், இறந்தவரின் வயது சான்று, FIR நகல் (பொருந்தினால்).",
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
        "text_mr": "समग्र शिक्षा अभियान पूर्व प्राथमिक ते इयत्ता 12 पर्यंतच्या शालेय शिक्षणासाठी एकात्मिक योजना आहे. मोफत पाठ्यपुस्तके, गणवेश, शालेय पायाभूत सुविधा, शिक्षक प्रशिक्षण आणि दिव्यांग मुलांसाठी वाहतूक मदत दिली जाते.",
        "text_ta": "சமக்ர சிக்ஷா அபியான் முன்-தொடக்கம் முதல் 12 ஆம் வகுப்பு வரையிலான பள்ளிக் கல்விக்கான ஒருங்கிணைந்த திட்டம். இலவச பாடப் புத்தகங்கள், சீருடை, பள்ளி கட்டமைப்பு, ஆசிரியர் பயிற்சி மற்றும் மாற்றுத்திறனாளிக் குழந்தைகளுக்கு போக்குவரத்து உதவி வழங்கப்படுகிறது.",
        "eligibility_mr": "सरकारी आणि सरकारी अनुदानित शाळांमध्ये पूर्व प्राथमिक ते इयत्ता 12 पर्यंत शिकणारी सर्व मुले. मुली, SC/ST आणि दिव्यांग मुलांवर विशेष लक्ष.",
        "eligibility_ta": "அரசு மற்றும் அரசு உதவி பெறும் பள்ளிகளில் முன்-தொடக்கம் முதல் 12 ஆம் வகுப்பு வரை படிக்கும் அனைத்துக் குழந்தைகளும். பெண்கள், SC/ST மற்றும் மாற்றுத்திறனாளிக் குழந்தைகளுக்கு சிறப்புக் கவனம்.",
        "how_to_apply_mr": "विद्यार्थ्यांसाठी अर्जाची गरज नाही. शाळांमार्फत लाभ आपोआप मिळतो. शाळा मुख्याध्यापक किंवा जिल्हा शिक्षण कार्यालयाशी संपर्क करा.",
        "how_to_apply_ta": "மாணவர்களுக்கு விண்ணப்பம் தேவையில்லை. பலன்கள் பள்ளிகள் மூலம் தானாகவே கிடைக்கும். பள்ளி தலைமை ஆசிரியர் அல்லது மாவட்டக் கல்வி அலுவலகத்தைத் தொடர்பு கொள்ளுங்கள்.",
        "documents_mr": "विद्यार्थ्यांसाठी कोणतीही कागदपत्रे लागत नाहीत. शाळेत प्रवेश पुरेसा. शाळा जिल्हा शिक्षण कार्यालयामार्फत निधीसाठी अर्ज करतात.",
        "documents_ta": "மாணவர்களுக்கு ஆவணங்கள் தேவையில்லை. பள்ளியில் சேர்ந்திருப்பதே போதுமானது. பள்ளிகள் மாவட்டக் கல்வி அலுவலகம் மூலம் நிதிக்கு விண்ணப்பிக்கின்றன.",
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
        "text_mr": "RBSK जन्मापासून 18 वर्षांपर्यंतच्या मुलांची 4D साठी मोफत आरोग्य तपासणी करतो: जन्मजात दोष, रोग, कमतरता आणि विकासातील विलंब. मोबाइल आरोग्य पथके शाळा आणि अंगणवाड्यांना भेट देतात. जिल्हा रुग्णालयांमध्ये मोफत उपचार मिळतो.",
        "text_ta": "RBSK பிறப்பு முதல் 18 வயது வரை குழந்தைகளுக்கு 4D-க்காக இலவச சுகாதாரப் பரிசோதனை செய்கிறது: பிறவிக் குறைபாடுகள், நோய்கள், குறைபாடுகள் மற்றும் வளர்ச்சித் தாமதங்கள். நடமாடும் சுகாதாரக் குழுக்கள் பள்ளிகள் மற்றும் அங்கன்வாடிகளுக்கு வருகின்றன. மாவட்ட மருத்துவமனைகளில் இலவச சிகிச்சை கிடைக்கும்.",
        "eligibility_mr": "नवजात ते 18 वर्षे वयाची सर्व मुले. सरकारी शाळा, अंगणवाडी केंद्रे आणि सरकारी आरोग्य केंद्रांमध्ये जन्मावेळी तपासणी.",
        "eligibility_ta": "புதிதாகப் பிறந்தவர் முதல் 18 வயது வரை அனைத்துக் குழந்தைகளும். அரசு பள்ளிகள், அங்கன்வாடி மையங்கள் மற்றும் அரசு சுகாதார நிறுவனங்களில் பிறக்கும்போது பரிசோதனை.",
        "how_to_apply_mr": "अर्जाची गरज नाही. RBSK मोबाइल आरोग्य पथके शाळा आणि अंगणवाड्यांना भेट देतात. रेफरलसाठी जवळच्या PHC किंवा जिल्हा रुग्णालयाशी संपर्क करा.",
        "how_to_apply_ta": "விண்ணப்பம் தேவையில்லை. RBSK நடமாடும் சுகாதாரக் குழுக்கள் பள்ளிகள் மற்றும் அங்கன்வாடிகளுக்கு வருகின்றன. பரிந்துரைக்கு அருகிலுள்ள PHC அல்லது மாவட்ட மருத்துவமனையைத் தொடர்பு கொள்ளுங்கள்.",
        "documents_mr": "कोणतीही कागदपत्रे लागत नाहीत. शाळा आणि अंगणवाड्यांमध्ये मोफत तपासणी. उपचार रेफरलसाठी: मुलाचे आधार किंवा जन्म दाखला.",
        "documents_ta": "ஆவணங்கள் தேவையில்லை. பள்ளிகள் மற்றும் அங்கன்வாடிகளில் இலவசப் பரிசோதனை. சிகிச்சை பரிந்துரைக்கு: குழந்தையின் ஆதார் அல்லது பிறப்புச் சான்றிதழ்.",
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
        "text_mr": "सौभाग्य योजना ग्रामीण आणि शहरी भागातील वीज नसलेल्या सर्व घरांना मोफत वीज कनेक्शन देते. बीपीएल घरांना मोफत कनेक्शन मिळते आणि एपीएल घरांना 500 रुपये 10 मासिक हप्त्यांत भरावे लागतात.",
        "text_ta": "சௌபாக்யா திட்டம் கிராமப்புற மற்றும் நகர்ப்புற பகுதிகளில் மின்சாரம் இல்லாத அனைத்து வீடுகளுக்கும் இலவச மின் இணைப்பு கொடுக்கிறது. BPL வீடுகளுக்கு இலவச இணைப்பு கிடைக்கும், APL வீடுகள் 500 ரூபாயை 10 மாத தவணைகளில் செலுத்த வேண்டும்.",
        "eligibility_mr": "भारतातील सर्व वीज नसलेली घरे. बीपीएल कुटुंबे, SC/ST कुटुंबे आणि दुर्गम भागातील कुटुंबांना प्राधान्य.",
        "eligibility_ta": "இந்தியாவில் மின்சாரம் இல்லாத அனைத்து வீடுகளும். BPL குடும்பங்கள், SC/ST குடும்பங்கள் மற்றும் தொலைதூர பகுதியில் உள்ளவர்களுக்கு முன்னுரிமை.",
        "how_to_apply_mr": "स्थानिक वीज वितरण कंपनी (DISCOM) किंवा ग्रामपंचायतशी संपर्क करा. आधार आणि BPL कार्ड (लागू असल्यास) घेऊन जा.",
        "how_to_apply_ta": "உள்ளூர் மின் விநியோக நிறுவனம் (DISCOM) அல்லது கிராம ஊராட்சியைத் தொடர்பு கொள்ளுங்கள். ஆதார் மற்றும் BPL கார்டு (பொருந்தினால்) எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, BPL कार्ड (लागू असल्यास), पत्त्याचा पुरावा. बीपीएल कुटुंबांसाठी इतर कोणतीही औपचारिकता नाही.",
        "documents_ta": "ஆதார் கார்டு, BPL கார்டு (பொருந்தினால்), முகவரிச் சான்று. BPL குடும்பங்களுக்கு வேறு சம்பிரதாயங்கள் எதுவும் இல்லை.",
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
        "text_mr": "स्वच्छ भारत ग्रामीण योजना ग्रामीण कुटुंबांना घरी शौचालय बांधण्यासाठी 12,000 रुपये देते. गावांमध्ये घन आणि द्रव कचरा व्यवस्थापनावरही भर दिला जातो. सर्व गावे उघड्यावर शौचमुक्त करणे हे ध्येय आहे.",
        "text_ta": "சுவச்சா பாரத் கிராமிண் திட்டம் கிராமப்புறக் குடும்பங்களுக்கு வீட்டில் கழிப்பறை கட்ட 12,000 ரூபாய் கொடுக்கிறது. கிராமங்களில் திடக்கழிவு மற்றும் திரவக்கழிவு மேலாண்மையிலும் கவனம் செலுத்தப்படுகிறது. அனைத்து கிராமங்களையும் திறந்தவெளி மலம் கழிப்பு இல்லாத நிலைக்கு கொண்டுவருவதே நோக்கம்.",
        "eligibility_mr": "शौचालय नसलेली ग्रामीण घरे. बीपीएल, SC/ST, लहान शेतकरी, भूमिहीन मजूर आणि महिला प्रमुख कुटुंबांना प्राधान्य.",
        "eligibility_ta": "கழிப்பறை இல்லாத கிராமப்புற வீடுகள். BPL, SC/ST, சிறு விவசாயிகள், நிலமற்ற தொழிலாளர்கள் மற்றும் பெண் தலைமையிலான குடும்பங்களுக்கு முன்னுரிமை.",
        "how_to_apply_mr": "ग्रामपंचायत कार्यालय किंवा खंड विकास कार्यालयात अर्ज करा. आधार, BPL कार्ड आणि बँक खाते माहिती घेऊन जा.",
        "how_to_apply_ta": "கிராம ஊராட்சி அலுவலகம் அல்லது வட்டார வளர்ச்சி அலுவலகத்தில் விண்ணப்பியுங்கள். ஆதார், BPL கார்டு மற்றும் வங்கிக் கணக்கு விவரங்களை எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, BPL कार्ड किंवा रेशन कार्ड, बँक खाते पासबुक, घराचा फोटो (शौचालय नसल्याचा पुरावा), पत्त्याचा पुरावा.",
        "documents_ta": "ஆதார் கார்டு, BPL கார்டு அல்லது ரேஷன் கார்டு, வங்கிக் கணக்கு பாஸ்புக், வீட்டின் புகைப்படம் (கழிப்பறை இல்லை என்ற சான்று), முகவரிச் சான்று.",
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
        "text_mr": "पीएम श्रम योगी मानधन असंघटित क्षेत्रातील कामगारांना 60 वर्षांनंतर दरमहा 3000 रुपये पेन्शन देते. कामगार वयानुसार दरमहा 55 ते 200 रुपये भरतात आणि सरकारही तितकीच रक्कम जमा करते.",
        "text_ta": "பிஎம் ஷ்ரம் யோகி மான்தன் அமைப்புசாரா தொழிலாளர்களுக்கு 60 வயதுக்குப் பிறகு மாதம் 3000 ரூபாய் ஓய்வூதியம் கொடுக்கிறது. தொழிலாளர்கள் வயதுக்கு ஏற்ப மாதம் 55 முதல் 200 ரூபாய் செலுத்துவார்கள், அரசும் அதே தொகையைச் செலுத்தும்.",
        "eligibility_mr": "18 ते 40 वर्षे वयाचे असंघटित कामगार ज्यांचे मासिक उत्पन्न 15,000 रुपयांपर्यंत आहे. EPFO/ESIC/NPS सदस्य आणि आयकरदाते पात्र नाहीत.",
        "eligibility_ta": "18 முதல் 40 வயது வரையிலான அமைப்புசாரா தொழிலாளர்கள், மாத வருமானம் 15,000 ரூபாய் வரை. EPFO/ESIC/NPS உறுப்பினர்கள் மற்றும் வருமான வரி செலுத்துபவர்கள் தகுதியற்றவர்.",
        "how_to_apply_mr": "जवळच्या CSC केंद्रात आधार आणि बचत बँक खाते घेऊन जा. CSC ऑपरेटर नोंदणी करेल. मासिक योगदान बँकेतून आपोआप कापले जाईल.",
        "how_to_apply_ta": "அருகிலுள்ள CSC மையத்திற்கு ஆதார் மற்றும் சேமிப்பு வங்கிக் கணக்குடன் செல்லுங்கள். CSC இயக்குநர் பதிவு செய்வார். மாதாந்திர பங்களிப்பு வங்கியிலிருந்து தானாகவே கழிக்கப்படும்.",
        "documents_mr": "आधार कार्ड, बचत बँक खाते माहिती, मोबाइल नंबर. इतर कोणतीही कागदपत्रे आवश्यक नाहीत.",
        "documents_ta": "ஆதார் கார்டு, சேமிப்பு வங்கிக் கணக்கு விவரங்கள், மொபைல் எண். வேறு ஆவணங்கள் தேவையில்லை.",
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
        "text_mr": "पीएम विश्वकर्मा पारंपारिक कारागीर आणि हस्तकलाकारांना मदत करते. मोफत कौशल्य प्रशिक्षण, साधने, 5% व्याजावर 3 लाख रुपयांपर्यंत बिनातारण कर्ज आणि डिजिटल पेमेंट प्रोत्साहन मिळते. सुतार, सोनार, कुंभार, लोहार अशा 18 व्यवसायांचा समावेश.",
        "text_ta": "பிஎம் விஸ்வகர்மா பாரம்பரிய கைவினைஞர்கள் மற்றும் கலைஞர்களுக்கு உதவுகிறது. இலவச திறன் பயிற்சி, கருவிகள், 5% வட்டியில் 3 லட்சம் ரூபாய் வரை பிணையமின்றி கடன் மற்றும் டிஜிட்டல் பணம் செலுத்தும் ஊக்கத்தொகை கிடைக்கும். தச்சர், பொற்கொல்லர், குயவர், கொல்லர் போன்ற 18 தொழில்கள் அடங்கும்.",
        "eligibility_mr": "18 अधिसूचित व्यवसायांमध्ये हात आणि साधनांनी काम करणारे पारंपारिक कारागीर आणि हस्तकलाकार. 18+ वर्षे वयाचे असावे आणि सरकारी कर्मचारी नसावे.",
        "eligibility_ta": "18 அறிவிக்கப்பட்ட தொழில்களில் கை மற்றும் கருவிகளால் வேலை செய்யும் பாரம்பரிய கைவினைஞர்கள் மற்றும் கலைஞர்கள். 18+ வயது இருக்க வேண்டும், அரசு ஊழியராக இருக்கக்கூடாது.",
        "how_to_apply_mr": "pmvishwakarma.gov.in वर आधार आणि मोबाइलने नोंदणी करा. ग्रामपंचायत/शहरी निकायाकडून सत्यापन आवश्यक. त्यानंतर प्रशिक्षण आणि कर्जासाठी अर्ज करा.",
        "how_to_apply_ta": "pmvishwakarma.gov.in-ல் ஆதார் மற்றும் மொபைலுடன் பதிவு செய்யுங்கள். கிராம ஊராட்சி/நகர்ப்புற உள்ளாட்சி சரிபார்ப்பு தேவை. பிறகு பயிற்சி மற்றும் கடனுக்கு விண்ணப்பியுங்கள்.",
        "documents_mr": "आधार कार्ड, मोबाइल नंबर, बँक खाते माहिती, जातीचा दाखला (लागू असल्यास), व्यवसायाशी संबंधित ओळखपत्र, पासपोर्ट साईज फोटो.",
        "documents_ta": "ஆதார் கார்டு, மொபைல் எண், வங்கிக் கணக்கு விவரங்கள், சாதிச் சான்றிதழ் (பொருந்தினால்), தொழில் தொடர்பான அடையாளச் சான்று, பாஸ்போர்ட் அளவு புகைப்படங்கள்.",
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
        "text_mr": "JSSK गर्भवती महिलांना सरकारी रुग्णालयांमध्ये मोफत प्रसूती, सी-सेक्शन, औषधे, तपासण्या, रक्त, आहार आणि घरापासून रुग्णालयापर्यंत मोफत वाहतूक देतो. 30 दिवसांपर्यंतच्या आजारी नवजात बालकांनाही मोफत उपचार मिळतो.",
        "text_ta": "JSSK கர்ப்பிணிப் பெண்களுக்கு அரசு மருத்துவமனைகளில் இலவச பிரசவம், சிசேரியன், மருந்துகள், பரிசோதனைகள், ரத்தம், உணவு மற்றும் வீட்டிலிருந்து மருத்துவமனை வரை இலவசப் போக்குவரத்து கொடுக்கிறது. 30 நாட்கள் வரை உள்ள நோய்வாய்ப்பட்ட பிறந்த குழந்தைகளுக்கும் இலவச சிகிச்சை கிடைக்கும்.",
        "eligibility_mr": "सरकारी आरोग्य केंद्रांमध्ये प्रसूती करणाऱ्या सर्व गर्भवती महिला आणि 30 दिवसांपर्यंतचे आजारी नवजात. कोणतीही उत्पन्न किंवा बीपीएल अट नाही.",
        "eligibility_ta": "அரசு சுகாதார நிறுவனங்களில் பிரசவிக்கும் அனைத்துக் கர்ப்பிணிப் பெண்களும் 30 நாட்கள் வரையிலான நோய்வாய்ப்பட்ட பிறந்த குழந்தைகளும். வருமானம் அல்லது BPL நிபந்தனை இல்லை.",
        "how_to_apply_mr": "प्रसूतीसाठी सरळ कोणत्याही सरकारी रुग्णालयात जा. सर्व सेवा कॅशलेस आहेत. आशा कार्यकर्ती वाहतूक आणि नोंदणीत मदत करेल.",
        "how_to_apply_ta": "பிரசவத்திற்கு நேரடியாக எந்த அரசு மருத்துவமனைக்கும் செல்லுங்கள். அனைத்து சேவைகளும் பணமில்லா முறையில். ஆஷா ஊழியர் போக்குவரத்து மற்றும் பதிவில் உதவுவார்.",
        "documents_mr": "आधार कार्ड किंवा कोणतेही सरकारी ओळखपत्र, गर्भावस्था नोंदणी पुरावा (असल्यास). कोणतेही कागदपत्र अनिवार्य नाही - सेवा नाकारता कामा नये.",
        "documents_ta": "ஆதார் கார்டு அல்லது ஏதாவது அரசு அடையாள அட்டை, கர்ப்பப் பதிவு சான்று (இருந்தால்). எந்த ஆவணமும் கட்டாயமில்லை - சேவை மறுக்கப்படக்கூடாது.",
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
        "text_mr": "पीएम कृषी सिंचाई योजना शेतकऱ्यांना ड्रिप सिंचन, स्प्रिंकलर आणि सूक्ष्म सिंचन उपकरणांवर सब्सिडी देते जेणेकरून पाण्याचा कार्यक्षम वापर होईल. लहान आणि सीमांत शेतकऱ्यांना 55% आणि इतरांना 45% सब्सिडी मिळते.",
        "text_ta": "பிஎம் கிருஷி சிஞ்சாய் திட்டம் விவசாயிகளுக்கு சொட்டு நீர்ப்பாசனம், தெளிப்பான்கள் மற்றும் நுண் நீர்ப்பாசன உபகரணங்களுக்கு மானியம் கொடுக்கிறது, இதனால் நீரை திறமையாகப் பயன்படுத்தலாம். சிறு மற்றும் குறு விவசாயிகளுக்கு 55% மற்றும் பிறருக்கு 45% மானியம் கிடைக்கும்.",
        "eligibility_mr": "स्वतःच्या किंवा भाडेपट्ट्याच्या शेतजमिनी असलेले सर्व शेतकरी. लहान आणि सीमांत शेतकरी, SC/ST शेतकरी आणि महिला शेतकऱ्यांना प्राधान्य.",
        "eligibility_ta": "சொந்த அல்லது குத்தகை விவசாய நிலம் உள்ள அனைத்து விவசாயிகளும். சிறு மற்றும் குறு விவசாயிகள், SC/ST விவசாயிகள் மற்றும் பெண் விவசாயிகளுக்கு முன்னுரிமை.",
        "how_to_apply_mr": "राज्य कृषी/फलोत्पादन विभागामार्फत अर्ज करा किंवा pmksy.gov.in वर नोंदणी करा. जमिनीचे कागदपत्रे, आधार आणि बँक माहिती घेऊन जा.",
        "how_to_apply_ta": "மாநில வேளாண்மை/தோட்டக்கலைத் துறை மூலம் விண்ணப்பியுங்கள் அல்லது pmksy.gov.in-ல் பதிவு செய்யுங்கள். நில ஆவணங்கள், ஆதார் மற்றும் வங்கி விவரங்களை எடுத்துச் செல்லுங்கள்.",
        "documents_mr": "आधार कार्ड, जमीन मालकी किंवा भाडेपट्टा कागदपत्रे, बँक खाते पासबुक, सिंचन उपकरणाचे कोटेशन, पासपोर्ट साईज फोटो.",
        "documents_ta": "ஆதார் கார்டு, நில உரிமை அல்லது குத்தகை ஆவணங்கள், வங்கிக் கணக்கு பாஸ்புக், நீர்ப்பாசன உபகரண விலைப்பட்டியல், பாஸ்போர்ட் அளவு புகைப்படங்கள்.",
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
        "text_mr": (
            "पीएम किसान सन्मान निधी बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: पीएम किसान मध्ये किती पैसे मिळतात?\n"
            "उत्तर: दरवर्षी 6,000 रुपये मिळतात, 2,000 रुपयांच्या 3 हप्त्यांमध्ये. हप्ते दर 4 महिन्यांनी थेट आधारशी जोडलेल्या बँक खात्यात येतात.\n\n"
            "प्रश्न: पीएम किसानसाठी कोणती कागदपत्रे लागतात?\n"
            "उत्तर: आधार कार्ड, आधारशी लिंक बँक खाते पासबुक, जमिनीची कागदपत्रे (खतौनी/खसरा), आणि मोबाइल नंबर. आधार-बँक लिंकिंग अनिवार्य आहे.\n\n"
            "प्रश्न: पीएम किसानचा पेमेंट स्टेटस कसा तपासायचा?\n"
            "उत्तर: pmkisan.gov.in वर 'Beneficiary Status' वर क्लिक करा. आधार नंबर, मोबाइल नंबर किंवा खाते नंबरने तपासा. हेल्पलाइन 155261 किंवा 011-24300606 वर कॉल करा.\n\n"
            "प्रश्न: पीएम किसानचे हप्ते कधी येतात?\n"
            "उत्तर: हप्ता 1 (एप्रिल-जुलै), हप्ता 2 (ऑगस्ट-नोव्हेंबर), हप्ता 3 (डिसेंबर-मार्च). प्रत्येक हप्ता 2,000 रुपये.\n\n"
            "प्रश्न: माझा पीएम किसानचा पैसा अडकला आहे, काय करू?\n"
            "उत्तर: सामान्य कारणे: (1) आधार बँकेशी लिंक नाही - बँकेत जाऊन लिंक करा, (2) आधार जुळत नाही - कृषी अधिकाऱ्याशी भेटा, (3) जमीन रेकॉर्ड सत्यापित नाही - पटवाऱ्याशी भेटा, (4) बँक माहिती चुकीची - pmkisan.gov.in वर अपडेट करा. 155261 वर कॉल करा.\n\n"
            "प्रश्न: भाडेकरू शेतकऱ्यांना पीएम किसान मिळतो का?\n"
            "उत्तर: नाही. फक्त ज्यांच्या नावावर जमीन आहे ते पात्र आहेत.\n\n"
            "प्रश्न: कोण पात्र नाही?\n"
            "उत्तर: आयकरदाते, सरकारी कर्मचारी (श्रेणी 4 सोडून), 10,000+ मासिक पेन्शनधारक, व्यावसायिक (डॉक्टर, इंजिनीअर, वकील, CA), संस्थात्मक जमीनधारक.\n\n"
            "प्रश्न: एका कुटुंबात किती लोकांना मिळेल?\n"
            "उत्तर: एका कुटुंबातून फक्त एकाच व्यक्तीला. कुटुंब म्हणजे पती, पत्नी आणि अल्पवयीन मुले.\n\n"
            "प्रश्न: eKYC कसे करायचे?\n"
            "उत्तर: pmkisan.gov.in > eKYC > आधार नंबर टाका > आधार-लिंक मोबाइलवर OTP ने सत्यापित करा. हप्ता मिळण्यासाठी eKYC अनिवार्य आहे."
        ),
        "text_ta": (
            "பிஎம் கிசான் சம்மான் நிதி பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: பிஎம் கிசான் திட்டத்தில் எவ்வளவு பணம் கிடைக்கும்?\n"
            "ப: ஆண்டுக்கு 6,000 ரூபாய், 2,000 ரூபாய் வீதம் 3 தவணைகளில் கிடைக்கும். ஒவ்வொரு 4 மாதத்திற்கும் ஆதாருடன் இணைக்கப்பட்ட வங்கிக் கணக்கில் நேரடியாக வரும்.\n\n"
            "கே: பிஎம் கிசானுக்கு என்ன ஆவணங்கள் தேவை?\n"
            "ப: ஆதார் அட்டை, ஆதாருடன் இணைக்கப்பட்ட வங்கிக் கணக்கு பாஸ்புக், நில உடைமை ஆவணங்கள் (கதௌனி/கஸ்ரா), மொபைல் எண். ஆதார்-வங்கி இணைப்பு கட்டாயம்.\n\n"
            "கே: பிஎம் கிசான் பணம் வந்ததா என்று எப்படி பார்ப்பது?\n"
            "ப: pmkisan.gov.in சென்று 'Beneficiary Status' கிளிக் செய்யுங்கள். ஆதார் எண், மொபைல் எண் அல்லது கணக்கு எண் மூலம் பாருங்கள். ஹெல்ப்லைன் 155261 அல்லது 011-24300606 அழைக்கவும்.\n\n"
            "கே: பிஎம் கிசான் தவணைகள் எப்போது வரும்?\n"
            "ப: தவணை 1 (ஏப்ரல்-ஜூலை), தவணை 2 (ஆகஸ்ட்-நவம்பர்), தவணை 3 (டிசம்பர்-மார்ச்). ஒவ்வொரு தவணையும் 2,000 ரூபாய்.\n\n"
            "கே: என் பிஎம் கிசான் பணம் நிறுத்தப்பட்டுள்ளது. என்ன செய்வது?\n"
            "ப: பொதுவான காரணங்கள்: (1) ஆதார் வங்கியுடன் இணைக்கப்படவில்லை - வங்கிக்குச் சென்று இணைக்கவும், (2) ஆதார் பொருந்தவில்லை - வேளாண் அதிகாரியை தொடர்பு கொள்ளவும், (3) நில பதிவுகள் சரிபார்க்கப்படவில்லை - பட்வாரியை தொடர்பு கொள்ளவும், (4) வங்கி விவரங்கள் தவறு - pmkisan.gov.in இல் புதுப்பிக்கவும். 155261 அழைக்கவும்.\n\n"
            "கே: குத்தகை விவசாயிகளுக்கு பிஎம் கிசான் கிடைக்குமா?\n"
            "ப: இல்லை. யாருடைய பெயரில் நிலம் உள்ளதோ அவர்கள் மட்டுமே தகுதி பெறுவார்கள்.\n\n"
            "கே: யாருக்கு தகுதி இல்லை?\n"
            "ப: வருமான வரி செலுத்துபவர்கள், அரசு ஊழியர்கள் (நிலை 4 தவிர), 10,000+ மாத ஓய்வூதியம் பெறுபவர்கள், தொழில் வல்லுநர்கள் (மருத்துவர், பொறியாளர், வழக்கறிஞர், CA), நிறுவன நிலவுடைமையாளர்கள்.\n\n"
            "கே: ஒரு குடும்பத்தில் எத்தனை பேருக்கு கிடைக்கும்?\n"
            "ப: ஒரு குடும்பத்தில் ஒருவருக்கு மட்டுமே. குடும்பம் என்றால் கணவன், மனைவி மற்றும் சிறு குழந்தைகள்.\n\n"
            "கே: eKYC எப்படி செய்வது?\n"
            "ப: pmkisan.gov.in > eKYC > ஆதார் எண் உள்ளிடவும் > ஆதாருடன் இணைக்கப்பட்ட மொபைலுக்கு வரும் OTP மூலம் சரிபார்க்கவும். தவணை பெற eKYC கட்டாயம்."
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
        "text_mr": (
            "आयुष्मान भारत (PM-JAY) बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: आयुष्मान भारत मध्ये किती आरोग्य विमा मिळतो?\n"
            "उत्तर: प्रति कुटुंब प्रति वर्ष 5 लाख रुपयांपर्यंत विमा. हे संपूर्ण कुटुंबासाठी आहे, प्रति व्यक्ती नाही.\n\n"
            "प्रश्न: मी आयुष्मान भारतसाठी पात्र आहे का, कसे कळेल?\n"
            "उत्तर: mera.pmjay.gov.in वर जा, मोबाइल नंबर टाका आणि OTP ने सत्यापित करा. किंवा 14555 वर कॉल करा. किंवा सूचीबद्ध रुग्णालयात आयुष्मान मित्राला भेटा.\n\n"
            "प्रश्न: कोणत्या रुग्णालयांमध्ये आयुष्मान कार्ड चालते?\n"
            "उत्तर: सर्व सरकारी रुग्णालये आणि सूचीबद्ध खाजगी रुग्णालये. pmjay.gov.in > Hospital Finder वर किंवा 14555 वर कॉल करून शोधा.\n\n"
            "प्रश्न: कोणत्या आजार आणि उपचार कव्हर होतात?\n"
            "उत्तर: 1,929 पेक्षा जास्त वैद्यकीय पॅकेजेस - शस्त्रक्रिया, उपचार, डे केअर, ICU, तपासण्या, औषधे आणि फॉलो-अप. आधीपासून असलेले आजार पहिल्या दिवसापासून कव्हर.\n\n"
            "प्रश्न: आयुष्मान कार्ड कसे बनवायचे?\n"
            "उत्तर: कोणत्याही सूचीबद्ध रुग्णालय, CSC केंद्र किंवा आयुष्मान आरोग्य मंदिरात आधार घेऊन जा. पात्रता सत्यापित होईल आणि ई-कार्ड जागेवर बनेल. कार्ड मोफत आहे.\n\n"
            "प्रश्न: आयुष्मान भारतमध्ये वयाची मर्यादा आहे का?\n"
            "उत्तर: नाही. कुटुंबातील सर्व सदस्य वय, लिंग किंवा कुटुंबाच्या आकाराची पर्वा न करता कव्हर आहेत.\n\n"
            "प्रश्न: दुसऱ्या राज्यात उपचार करता येतात का?\n"
            "उत्तर: होय. आयुष्मान भारत संपूर्ण भारतात पोर्टेबल आहे. कोणत्याही राज्यातील सूचीबद्ध रुग्णालयात उपचार करता येतात.\n\n"
            "प्रश्न: रुग्णालयाने उपचार नाकारले तर?\n"
            "उत्तर: 14555 वर कॉल करून तक्रार करा. सूचीबद्ध रुग्णालये पात्र लाभार्थ्यांना उपचार नाकारू शकत नाहीत.\n\n"
            "प्रश्न: रुग्णालयात काही पैसे द्यावे लागतात का?\n"
            "उत्तर: नाही. उपचार पूर्णपणे कॅशलेस आणि पेपरलेस आहेत. रुग्णालय थेट विमा कंपनीकडून दावा करते."
        ),
        "text_ta": (
            "ஆயுஷ்மான் பாரத் (PM-JAY) பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: ஆயுஷ்மான் பாரத்தில் எவ்வளவு மருத்துவ காப்பீடு கிடைக்கும்?\n"
            "ப: ஒரு குடும்பத்திற்கு ஆண்டுக்கு 5 லட்சம் ரூபாய் வரை காப்பீடு. இது முழு குடும்பத்திற்கும், தனி நபருக்கு அல்ல.\n\n"
            "கே: நான் ஆயுஷ்மான் பாரத்திற்கு தகுதியானவனா என்றால் எப்படி தெரிந்துகொள்வது?\n"
            "ப: mera.pmjay.gov.in சென்று மொபைல் எண் உள்ளிட்டு OTP மூலம் சரிபார்க்கவும். அல்லது 14555 அழைக்கவும். அல்லது பட்டியலிடப்பட்ட மருத்துவமனையில் ஆயுஷ்மான் மித்ராவை சந்திக்கவும்.\n\n"
            "கே: எந்த மருத்துவமனைகளில் ஆயுஷ்மான் அட்டை ஏற்கப்படும்?\n"
            "ப: அனைத்து அரசு மருத்துவமனைகள் மற்றும் பட்டியலிடப்பட்ட தனியார் மருத்துவமனைகள். pmjay.gov.in > Hospital Finder அல்லது 14555 அழைக்கவும்.\n\n"
            "கே: என்னென்ன நோய்கள் மற்றும் சிகிச்சைகள் கவர் ஆகும்?\n"
            "ப: 1,929க்கும் மேற்பட்ட மருத்துவ தொகுப்புகள் - அறுவை சிகிச்சை, சிகிச்சை, டே கேர், ICU, பரிசோதனைகள், மருந்துகள் மற்றும் பின்தொடர் சிகிச்சை. ஏற்கனவே உள்ள நோய்களும் முதல் நாளிலிருந்தே கவர்.\n\n"
            "கே: ஆயுஷ்மான் அட்டை எப்படி பெறுவது?\n"
            "ப: பட்டியலிடப்பட்ட மருத்துவமனை, CSC மையம் அல்லது ஆயுஷ்மான் ஆரோக்கிய மந்திரில் ஆதார் எடுத்துச் செல்லுங்கள். தகுதி சரிபார்க்கப்பட்டு இ-அட்டை அங்கேயே தயாரிக்கப்படும். அட்டை இலவசம்.\n\n"
            "கே: ஆயுஷ்மான் பாரத்தில் வயது வரம்பு உள்ளதா?\n"
            "ப: இல்லை. குடும்பத்தின் அனைத்து உறுப்பினர்களும் வயது, பாலினம் அல்லது குடும்ப அளவைப் பொருட்படுத்தாமல் கவர் ஆவார்கள்.\n\n"
            "கே: வேறு மாநிலத்தில் சிகிச்சை பெற முடியுமா?\n"
            "ப: ஆம். ஆயுஷ்மான் பாரத் இந்தியா முழுவதும் பயன்படுத்தலாம். எந்த மாநிலத்திலும் உள்ள பட்டியலிடப்பட்ட மருத்துவமனையில் சிகிச்சை பெறலாம்.\n\n"
            "கே: மருத்துவமனை சிகிச்சை மறுத்தால் என்ன செய்வது?\n"
            "ப: 14555 அழைத்து புகார் செய்யுங்கள். பட்டியலிடப்பட்ட மருத்துவமனைகள் தகுதியான பயனாளிகளுக்கு சிகிச்சை மறுக்க முடியாது.\n\n"
            "கே: மருத்துவமனையில் ஏதாவது பணம் செலுத்த வேண்டுமா?\n"
            "ப: இல்லை. சிகிச்சை முழுமையாக கேஷ்லெஸ் மற்றும் பேப்பர்லெஸ். மருத்துவமனை நேரடியாக காப்பீட்டு நிறுவனத்திடம் கோருகிறது."
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
        "text_mr": (
            "मनरेगा बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: मनरेगामध्ये किती दिवस काम मिळते?\n"
            "उत्तर: प्रत्येक ग्रामीण कुटुंबाला प्रति आर्थिक वर्षात 100 दिवस हमी काम.\n\n"
            "प्रश्न: मनरेगामध्ये रोज किती मजुरी मिळते?\n"
            "उत्तर: राज्यानुसार दररोज 200 ते 350 रुपये. दरवर्षी सुधारित होते. nrega.nic.in वर तुमच्या राज्याचा दर पहा.\n\n"
            "प्रश्न: मनरेगा जॉब कार्ड कसे बनवायचे?\n"
            "उत्तर: ग्राम पंचायतीत आधार, फोटो आणि बँक माहिती घेऊन अर्ज करा. 15 दिवसांत जॉब कार्ड मिळेल. हे मोफत आहे.\n\n"
            "प्रश्न: मनरेगामध्ये काम कसे मागायचे?\n"
            "उत्तर: ग्राम पंचायतीत लेखी अर्ज द्या. 15 दिवसांत काम मिळायला हवे. अर्जाची पावती जपून ठेवा.\n\n"
            "प्रश्न: 15 दिवसांत काम न मिळाल्यास?\n"
            "उत्तर: बेरोजगारी भत्ता मिळेल - पहिले 30 दिवस मजुरीचा एक-चतुर्थांश, त्यानंतर अर्धा. nrega.nic.in वर तक्रार नोंदवा.\n\n"
            "प्रश्न: मनरेगा पेमेंट स्टेटस कसा पाहायचा?\n"
            "उत्तर: nrega.nic.in > तुमचे राज्य, जिल्हा, ब्लॉक, पंचायत निवडा > जॉब कार्ड आणि पेमेंट तपशील पहा.\n\n"
            "प्रश्न: महिला मनरेगामध्ये काम करू शकतात का?\n"
            "उत्तर: होय. किमान एक-तृतीयांश कामाचे दिवस महिलांसाठी राखीव आहेत. पुरुष आणि महिलांना समान मजुरी.\n\n"
            "प्रश्न: मनरेगामध्ये कोणत्या प्रकारचे काम होते?\n"
            "उत्तर: जलसंधारण, दुष्काळ प्रतिबंध, जमीन विकास, ग्रामीण रस्ते, पूर नियंत्रण, सिंचन कालवे, पारंपरिक जलस्रोतांचे नूतनीकरण.\n\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: nrega.nic.in > तक्रार विभाग, किंवा 1800-111-555 वर कॉल करा, किंवा जिल्हा कार्यक्रम समन्वयकाला लिहा."
        ),
        "text_ta": (
            "மகாத்மா காந்தி தேசிய ஊரக வேலை உறுதித் திட்டம் (MGNREGA) பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: MGNREGA இல் எத்தனை நாட்கள் வேலை கிடைக்கும்?\n"
            "ப: ஒவ்வொரு கிராமப்புற குடும்பத்திற்கும் நிதியாண்டுக்கு 100 நாட்கள் உத்தரவாத வேலை.\n\n"
            "கே: MGNREGA இல் தினசரி ஊதியம் எவ்வளவு?\n"
            "ப: மாநிலத்தைப் பொறுத்து நாளுக்கு 200 முதல் 350 ரூபாய். ஆண்டுதோறும் திருத்தப்படும். nrega.nic.in இல் உங்கள் மாநில விகிதத்தைப் பாருங்கள்.\n\n"
            "கே: MGNREGA ஜாப் கார்டு எப்படி பெறுவது?\n"
            "ப: ஆதார், புகைப்படங்கள், வங்கி விவரங்களுடன் கிராம பஞ்சாயத்தில் விண்ணப்பியுங்கள். 15 நாட்களில் ஜாப் கார்டு கிடைக்கும். இது இலவசம்.\n\n"
            "கே: MGNREGA இல் வேலை எப்படி கேட்பது?\n"
            "ப: கிராம பஞ்சாயத்தில் எழுத்துப்பூர்வ விண்ணப்பம் கொடுங்கள். 15 நாட்களுக்குள் வேலை கிடைக்க வேண்டும். விண்ணப்ப ரசீதை பத்திரமாக வைக்கவும்.\n\n"
            "கே: 15 நாட்களுக்குள் வேலை கிடைக்கவில்லை என்றால்?\n"
            "ப: வேலையின்மை கொடுப்பனவு கிடைக்கும் - முதல் 30 நாட்கள் ஊதியத்தின் கால் பங்கு, பிறகு பாதி. nrega.nic.in இல் புகார் செய்யுங்கள்.\n\n"
            "கே: MGNREGA பணம் வந்ததா என்று எப்படி பார்ப்பது?\n"
            "ப: nrega.nic.in > உங்கள் மாநிலம், மாவட்டம், வட்டம், பஞ்சாயத்தைத் தேர்ந்தெடுங்கள் > ஜாப் கார்டு மற்றும் பணம் செலுத்திய விவரங்களைப் பாருங்கள்.\n\n"
            "கே: பெண்கள் MGNREGA இல் வேலை செய்ய முடியுமா?\n"
            "ப: ஆம். குறைந்தது மூன்றில் ஒரு பங்கு வேலை நாட்கள் பெண்களுக்கு ஒதுக்கப்பட்டுள்ளன. ஆண்களுக்கும் பெண்களுக்கும் சம ஊதியம்.\n\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: nrega.nic.in > புகார் பிரிவு, அல்லது 1800-111-555 அழைக்கவும், அல்லது மாவட்ட திட்ட ஒருங்கிணைப்பாளருக்கு எழுதுங்கள்."
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
        "text_mr": (
            "पीएम आवास योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: पीएम आवास योजनेत किती पैसे मिळतात?\n"
            "उत्तर: ग्रामीण (PMAY-G): मैदानी भागात 1.20 लाख, डोंगराळ भागात 1.30 लाख. शहरी (PMAY-U): गृहकर्जावर 3-6.5% व्याज सवलत - EWS/LIG ला 2.67 लाख, MIG-I ला 2.35 लाख, MIG-II ला 2.30 लाख सवलत.\n\n"
            "प्रश्न: पीएम आवास योजनेसाठी कोण पात्र आहे?\n"
            "उत्तर: ज्यांच्याकडे भारतात कुठेही पक्के घर नाही. EWS (वार्षिक उत्पन्न 3 लाखांपर्यंत), LIG (3-6 लाख), MIG-I (6-12 लाख), MIG-II (12-18 लाख).\n\n"
            "प्रश्न: अर्ज कसा करायचा?\n"
            "उत्तर: ग्रामीण: ग्राम पंचायतीत अर्ज करा. शहरी: pmaymis.gov.in वर ऑनलाइन किंवा CSC/शहरी स्थानिक संस्थेत. आधार, उत्पन्न प्रमाणपत्र आणि बँक माहिती न्या.\n\n"
            "प्रश्न: अर्जाची स्थिती कशी तपासायची?\n"
            "उत्तर: ग्रामीण: pmayg.nic.in वर नाव किंवा नोंदणी क्रमांकाने शोधा. शहरी: pmaymis.gov.in > Track Your Assessment Status > आधार किंवा असेसमेंट ID टाका.\n\n"
            "प्रश्न: पैसे कधी येतात?\n"
            "उत्तर: ग्रामीण: निवड आणि पहिल्या हप्त्यासाठी 6-12 महिने. बांधकाम प्रगतीनुसार 3-4 हप्त्यांमध्ये पैसे येतात. शहरी: कर्ज वितरणानंतर 3-4 महिन्यांत सवलत.\n\n"
            "प्रश्न: आधीच घर असेल तर अर्ज करता येतो का?\n"
            "उत्तर: नाही. तुम्ही किंवा कुटुंबातील कोणाकडेही भारतात पक्के घर असल्यास पात्र नाही.\n\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: 1800-11-6163 (टोल-फ्री) वर कॉल करा. PMAY पोर्टलवर तक्रार नोंदवा. किंवा जिल्हाधिकारी/नगर आयुक्तांशी संपर्क करा."
        ),
        "text_ta": (
            "பிஎம் ஆவாஸ் யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: பிஎம் ஆவாஸ் யோஜனாவில் எவ்வளவு பணம் கிடைக்கும்?\n"
            "ப: கிராமம் (PMAY-G): சமவெளியில் 1.20 லட்சம், மலைப்பகுதியில் 1.30 லட்சம். நகரம் (PMAY-U): வீட்டுக் கடனுக்கு 3-6.5% வட்டி மானியம் - EWS/LIG க்கு 2.67 லட்சம், MIG-I க்கு 2.35 லட்சம், MIG-II க்கு 2.30 லட்சம் மானியம்.\n\n"
            "கே: பிஎம் ஆவாஸ் யோஜனாவுக்கு யார் தகுதி?\n"
            "ப: இந்தியாவில் எங்கும் பக்கா வீடு இல்லாத குடும்பங்கள். EWS (ஆண்டு வருமானம் 3 லட்சம் வரை), LIG (3-6 லட்சம்), MIG-I (6-12 லட்சம்), MIG-II (12-18 லட்சம்).\n\n"
            "கே: எப்படி விண்ணப்பிப்பது?\n"
            "ப: கிராமம்: கிராம பஞ்சாயத்தில் விண்ணப்பியுங்கள். நகரம்: pmaymis.gov.in இல் ஆன்லைனில் அல்லது CSC/நகர உள்ளாட்சியில். ஆதார், வருமானச் சான்றிதழ், வங்கி விவரங்கள் எடுத்துச் செல்லுங்கள்.\n\n"
            "கே: விண்ணப்ப நிலை எப்படி பார்ப்பது?\n"
            "ப: கிராமம்: pmayg.nic.in இல் பெயர் அல்லது பதிவு எண் மூலம் தேடுங்கள். நகரம்: pmaymis.gov.in > Track Your Assessment Status > ஆதார் அல்லது அசெஸ்மெண்ட் ID உள்ளிடவும்.\n\n"
            "கே: பணம் எப்போது வரும்?\n"
            "ப: கிராமம்: தேர்வு மற்றும் முதல் தவணைக்கு 6-12 மாதங்கள். கட்டுமான முன்னேற்றத்தின் அடிப்படையில் 3-4 தவணைகளில் பணம் வரும். நகரம்: கடன் வழங்கிய 3-4 மாதங்களில் மானியம்.\n\n"
            "கே: ஏற்கனவே வீடு இருந்தால் விண்ணப்பிக்க முடியுமா?\n"
            "ப: இல்லை. நீங்கள் அல்லது குடும்பத்தில் யாருக்காவது இந்தியாவில் எங்காவது பக்கா வீடு இருந்தால் தகுதி இல்லை.\n\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: 1800-11-6163 (கட்டணமில்லா) அழைக்கவும். PMAY போர்ட்டலில் புகார் பதிவு செய்யவும். அல்லது மாவட்ட ஆட்சியர்/நகர ஆணையரை தொடர்பு கொள்ளவும்."
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
        "text_mr": (
            "सुकन्या समृद्धी योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: सुकन्या समृद्धीचा सध्याचा व्याजदर किती आहे?\n"
            "उत्तर: व्याजदर सरकार दर तिमाहीत ठरवते. साधारणपणे 8-8.2% वार्षिक, लहान बचत योजनांमध्ये सर्वाधिक.\n\n"
            "प्रश्न: किमान आणि कमाल ठेव किती?\n"
            "उत्तर: किमान 250 रुपये वार्षिक, कमाल 1.5 लाख वार्षिक. खाते उघडल्यानंतर पहिले 15 वर्षे जमा करावे लागते.\n\n"
            "प्रश्न: खाते कधी परिपक्व होते?\n"
            "उत्तर: खाते उघडल्यापासून 21 वर्षांनी किंवा मुलीचे 18 वर्षांनंतर लग्न (जे आधी घडेल). 18 वर्षांनंतर शिक्षणासाठी 50% काढता येते.\n\n"
            "प्रश्न: कर लाभ काय आहे?\n"
            "उत्तर: कलम 80C अंतर्गत तिहेरी लाभ: 1.5 लाखांपर्यंत ठेवीवर कर सूट, व्याज करमुक्त, आणि परिपक्वता रक्कम करमुक्त.\n\n"
            "प्रश्न: एका कुटुंबात किती खाती उघडता येतात?\n"
            "उत्तर: कमाल 2 (एका मुलीचे एक). जुळ्या मुलींसाठी पुरावा देऊन तिसरे खाते उघडता येते.\n\n"
            "प्रश्न: खाते दुसऱ्या बँक किंवा पोस्ट ऑफिसमध्ये हस्तांतरित करता येते का?\n"
            "उत्तर: होय. खाते भारतात कुठेही एका पोस्ट ऑफिस/बँकेतून दुसऱ्याकडे हस्तांतरित करता येते.\n\n"
            "प्रश्न: वर्षात जमा न केल्यास काय होते?\n"
            "उत्तर: खाते निष्क्रिय होते. सक्रिय करण्यासाठी प्रति वर्ष 50 रुपये दंड आणि 250 रुपये किमान ठेव द्यावी लागते."
        ),
        "text_ta": (
            "சுகன்யா சம்ரிதி யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: சுகன்யா சம்ரிதியின் தற்போதைய வட்டி விகிதம் என்ன?\n"
            "ப: வட்டி விகிதத்தை அரசு ஒவ்வொரு காலாண்டிலும் நிர்ணயிக்கிறது. பொதுவாக ஆண்டுக்கு 8-8.2%, சிறு சேமிப்பு திட்டங்களில் அதிகபட்சம்.\n\n"
            "கே: குறைந்தபட்ச மற்றும் அதிகபட்ச வைப்பு எவ்வளவு?\n"
            "ப: குறைந்தபட்சம் ஆண்டுக்கு 250 ரூபாய், அதிகபட்சம் ஆண்டுக்கு 1.5 லட்சம். கணக்கு திறந்த பிறகு முதல் 15 ஆண்டுகள் வைப்பு செய்ய வேண்டும்.\n\n"
            "கே: கணக்கு எப்போது முதிர்ச்சி அடையும்?\n"
            "ப: கணக்கு திறந்த 21 ஆண்டுகளுக்குப் பிறகு அல்லது பெண் 18 வயதுக்குப் பிறகு திருமணம் (எது முதலில் நடக்கிறதோ). 18 வயதுக்குப் பிறகு கல்விக்காக 50% எடுக்கலாம்.\n\n"
            "கே: வரி சலுகை என்ன?\n"
            "ப: பிரிவு 80C கீழ் மூன்று மடங்கு சலுகை: 1.5 லட்சம் வரை வைப்புக்கு வரி விலக்கு, வட்டி வரி இல்லை, முதிர்வுத் தொகை வரி இல்லை.\n\n"
            "கே: ஒரு குடும்பத்தில் எத்தனை கணக்குகள் திறக்கலாம்?\n"
            "ப: அதிகபட்சம் 2 (ஒரு பெண் குழந்தைக்கு ஒன்று). இரட்டை பெண் குழந்தைகளுக்கு சான்றுடன் மூன்றாவது கணக்கு திறக்கலாம்.\n\n"
            "கே: ஒரு வருடத்தில் வைப்பு செய்யவில்லை என்றால் என்ன ஆகும்?\n"
            "ப: கணக்கு செயலிழக்கும். மீண்டும் செயல்படுத்த வருடத்திற்கு 50 ரூபாய் அபராதம் மற்றும் 250 ரூபாய் குறைந்தபட்ச வைப்பு செலுத்த வேண்டும்."
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
        "text_mr": (
            "पीएम मुद्रा योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: मुद्रा कर्ज किती प्रकारचे आहेत?\n"
            "उत्तर: चार श्रेण्या: शिशु (50,000 पर्यंत), किशोर (50,001 ते 5 लाख), तरुण (5 ते 10 लाख), तरुण प्लस (10 ते 20 लाख).\n\n"
            "प्रश्न: मुद्रा कर्जावर व्याजदर किती?\n"
            "उत्तर: बँकेनुसार 7-12% वार्षिक. कोणताही निश्चित दर नाही - बँक जोखमीनुसार ठरवते.\n\n"
            "प्रश्न: जामीन किंवा तारण लागते का?\n"
            "उत्तर: 10 लाखांपर्यंत कोणतेही तारण नाही. तरुण प्लस (10 लाखांपेक्षा जास्त) मध्ये बँक तारण मागू शकते.\n\n"
            "प्रश्न: कोणत्या व्यवसायांसाठी मुद्रा कर्ज मिळते?\n"
            "उत्तर: कोणताही शेती-बाहेरचा छोटा व्यवसाय: दुकान, फेरीवाला, शिंपी, दुरुस्ती, सलून, खाद्य स्टॉल, छोटे उत्पादन, वाहतूक, कारागीर इ.\n\n"
            "प्रश्न: मुद्रा कर्ज कुठून घ्यायचे?\n"
            "उत्तर: कोणत्याही व्यापारी बँक, ग्रामीण बँक, स्मॉल फायनान्स बँक, NBFC किंवा MFI मधून. udyamimitra.in किंवा mudra.org.in वर ऑनलाइनही.\n\n"
            "प्रश्न: शेतीसाठी मुद्रा कर्ज मिळेल का?\n"
            "उत्तर: नाही. मुद्रा कर्ज फक्त शेती-बाहेरच्या व्यवसायांसाठी. शेतीसाठी किसान क्रेडिट कार्ड किंवा इतर कृषी कर्ज योजनांत अर्ज करा."
        ),
        "text_ta": (
            "பிஎம் முத்ரா யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: முத்ரா கடன் எத்தனை வகை?\n"
            "ப: நான்கு வகைகள்: சிசு (50,000 வரை), கிஷோர் (50,001 முதல் 5 லட்சம்), தருண் (5 முதல் 10 லட்சம்), தருண் பிளஸ் (10 முதல் 20 லட்சம்).\n\n"
            "கே: முத்ரா கடனுக்கு வட்டி விகிதம் என்ன?\n"
            "ப: வங்கியைப் பொறுத்து ஆண்டுக்கு 7-12%. நிலையான விகிதம் இல்லை - வங்கி ஆபத்தின் அடிப்படையில் தீர்மானிக்கும்.\n\n"
            "கே: ஜாமீன் அல்லது பிணை தேவையா?\n"
            "ப: 10 லட்சம் வரை பிணை தேவையில்லை. தருண் பிளஸ் (10 லட்சத்திற்கு மேல்) இல் வங்கி பிணை கேட்கலாம்.\n\n"
            "கே: எந்த தொழில்களுக்கு முத்ரா கடன் கிடைக்கும்?\n"
            "ப: விவசாயம் அல்லாத எந்த சிறு தொழிலுக்கும்: கடை, தெருவோர வியாபாரி, தையல்காரர், பழுது பார்ப்பு, சலூன், உணவுக் கடை, சிறு உற்பத்தி, போக்குவரத்து, கைவினைஞர்.\n\n"
            "கே: முத்ரா கடன் எங்கு பெறுவது?\n"
            "ப: எந்த வணிக வங்கி, கிராமிய வங்கி, சிறு நிதி வங்கி, NBFC அல்லது MFI யிடம். udyamimitra.in அல்லது mudra.org.in இல் ஆன்லைனிலும்.\n\n"
            "கே: விவசாயத்திற்கு முத்ரா கடன் கிடைக்குமா?\n"
            "ப: இல்லை. முத்ரா கடன் விவசாயம் அல்லாத தொழில்களுக்கு மட்டுமே. விவசாயத்திற்கு கிசான் கிரெடிட் கார்டு அல்லது பிற வேளாண் கடன் திட்டங்களில் விண்ணப்பிக்கவும்."
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
        "text_mr": (
            "पीएम फसल बीमा योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: शेतकऱ्यांना किती प्रीमियम द्यावे लागते?\n"
            "उत्तर: खरीप पिके: विमा रक्कमेचे 2%. रब्बी पिके: 1.5%. व्यापारी/फळबागायती पिके: 5%. उरलेले प्रीमियम सरकार देते.\n\n"
            "प्रश्न: कोणत्या पिकांचे नुकसान कव्हर होते?\n"
            "उत्तर: नैसर्गिक आपदा (पूर, दुष्काळ, गारापीट, चक्रीवादळ, कीड), पेरणी रोखलेली, मध्य-हंगाम प्रतिकूलता, कापणीनंतर नुकसान (14 दिवसांपर्यंत), स्थानिक आपदा.\n\n"
            "प्रश्न: फसल विमा दावा कसा करायचा?\n"
            "उत्तर: फसल नुकसानीच्या 72 तासांत विमा कंपनी, बँक, कृषी कार्यालय किंवा Crop Insurance App वर कळवा. 14447 वर कॉल करा.\n\n"
            "प्रश्न: दावा कित्या दिवसांत मिळतो?\n"
            "उत्तर: कापणीनंतर 2 महिन्यांत दावा निपटारा व्हायला हवा. उशीर होऊन विमा कंपनी 12% व्याज देते.\n\n"
            "प्रश्न: फसल विमा अनिवार्य आहे का?\n"
            "उत्तर: खरीप 2020 पासून सर्व शेतकऱ्यांसाठी ऐच्छिक. कर्ज घेणारे शेतकरीही अंतिम तारखेपूर्वी बँकेला कळवून बाहेर पडू शकतात.\n\n"
            "प्रश्न: दाव्याची स्थिती कशी तपासायची?\n"
            "उत्तर: pmfby.gov.in > Application Status, किंवा Crop Insurance App, किंवा 14447 वर कॉल करा."
        ),
        "text_ta": (
            "பிஎம் பசல் பீமா யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: விவசாயிகள் எவ்வளவு பிரீமியம் கட்ட வேண்டும்?\n"
            "ப: கரிப் பயிர்கள்: காப்பீட்டத் தொகையின் 2%. ரபி பயிர்கள்: 1.5%. வணிக/தோட்டக் கலை பயிர்கள்: 5%. மீதி பிரீமியத்தை அரசு செலுத்துகிறது.\n\n"
            "கே: என்னென்ன பயிர் நஷ்டங்கள் கவர் ஆகும்?\n"
            "ப: புயல் பேரழிவுகள் (வெள்ளம், வறட்சி, ஆலங்கட்டி, புயல், பூச்சி), விதைப்பு தடுக்கப்பட்டது, மத்தியப் பருவ பாதிப்பு, அறுவடைக்குப் பிறகான நஷ்டம் (14 நாட்கள் வரை), தல பேரழிவு.\n\n"
            "கே: பயிர் காப்பீட்டு கோரிக்கை எப்படி செய்வது?\n"
            "ப: பயிர் நஷ்டத்தின் 72 மணி நேரத்தில் காப்பீட்டு நிறுவனம், வங்கி, வேளாண் அலுவலகம் அல்லது Crop Insurance App இல் தெரிவிக்கவும். 14447 அழைக்கவும்.\n\n"
            "கே: கோரிக்கை எப்போது தீர்க்கப்படும்?\n"
            "ப: அறுவடைக்குப் பிறகு 2 மாதங்களில் கோரிக்கை தீர்க்கப்பட வேண்டும். தாமதமானால் காப்பீட்டு நிறுவனம் 12% வட்டி கொடுக்கும்.\n\n"
            "கே: பயிர் காப்பீடு கட்டாயமா?\n"
            "ப: கரிப் 2020 முதல் அனைத்து விவசாயிகளுக்கும் தன்னார்வம். கடன் பெற்ற விவசாயிகளும் கடைசி தேதிக்கு முன் வங்கிக்கு தெரிவித்து விலகலாம்.\n\n"
            "கே: கோரிக்கை நிலை எப்படி பார்ப்பது?\n"
            "ப: pmfby.gov.in > Application Status, அல்லது Crop Insurance App, அல்லது 14447 அழைக்கவும்."
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
        "text_mr": (
            "अटल पेंशन योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: किती पेंशन मिळेल?\n"
            "उत्तर: तुम्ही निवडा: 60 वर्षांनंतर दरमहा 1,000, 2,000, 3,000, 4,000 किंवा 5,000 रुपये. जास्त पेंशन = जास्त मासिक योगदान.\n\n"
            "प्रश्न: दरमहा किती द्यायचे?\n"
            "उत्तर: वय आणि निवडलेल्या पेंशनवर अवलंबून. उदाहरण: 5,000 रुपये पेंशनसाठी - 18 वर्षी सामील होताना 210/महिना, 30 वर्षी 577/महिना, 40 वर्षी 1,454/महिना.\n\n"
            "प्रश्न: माझ्या मृत्यूनंतर काय होईल?\n"
            "उत्तर: पती/पत्नीला आयुष्यभर तीच पेंशन मिळेल. त्यांच्या मृत्यूनंतर जमा रक्कम नॉमिनीला परत.\n\n"
            "प्रश्न: APY बॅलन्स कसे चेक करायचे?\n"
            "उत्तर: बँकेच्या नेट बँकिंग/मोबाइल बँकिंगमधून, किंवा enps.nsdl.com वर, किंवा बँक शाखेत विचारा.\n\n"
            "प्रश्न: पेंशन रक्कम नंतर बदलता येते का?\n"
            "उत्तर: होय. एप्रिलमध्ये वर्षात एकदा वाढवता किंवा कमी करता येते. बँकेत जाऊन विनंती करा.\n\n"
            "प्रश्न: मासिक योगदान चुकले तर?\n"
            "उत्तर: दरमहा 1-10 रुपये दंड. 6 महिने थकबाकी असल्यास खाते गोठवतात. 12 महिन्यांनंतर बंद होते."
        ),
        "text_ta": (
            "அடல் ஓய்வூதிய திட்டம் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: எவ்வளவு ஓய்வூதியம் கிடைக்கும்?\n"
            "ப: நீங்கள் தேர்வு செய்யுங்கள்: 60 வயதுக்குப் பிறகு மாதம் 1,000, 2,000, 3,000, 4,000 அல்லது 5,000 ரூபாய். அதிக ஓய்வூதியம் = அதிக மாத செலுத்துதல்.\n\n"
            "கே: மாதத்திற்கு எவ்வளவு செலுத்த வேண்டும்?\n"
            "ப: உங்கள் வயது மற்றும் தேர்வு செய்த ஓய்வூதியத்தைப் பொறுத்து. உதாரணம்: 5,000 ரூபாய் ஓய்வூதியத்திற்கு - 18 வயதில் சேர்ந்தால் 210/மாதம், 30 வயதில் 577/மாதம், 40 வயதில் 1,454/மாதம்.\n\n"
            "கே: நான் இறந்த பிறகு என்ன நடக்கும்?\n"
            "ப: கணவன்/மனைவிக்கு வாழ்நாள் அதே ஓய்வூதியம் கிடைக்கும். அவர்கள் இறந்த பிறகு ஜமா தொகை நாமினிக்கு தரப்படும்.\n\n"
            "கே: APY கணக்கு இருப்பை எப்படி பார்ப்பது?\n"
            "ப: வங்கியின் நெட் பேங்கிங்/மொபைல் பேங்கிங் மூலம், அல்லது enps.nsdl.com இல், அல்லது வங்கிக் கிளையில் கேளுங்கள்.\n\n"
            "கே: மாத செலுத்துதல் தவறியோ என்ன ஆகும்?\n"
            "ப: மாதத்திற்கு 1-10 ரூபாய் அபராதம். 6 மாதங்கள் முடங்கியிருந்தால் கணக்கு உறையும். 12 மாதங்கள் பிறகு மூடப்படும்."
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
        "text_mr": (
            "पीएम स्वनिधी बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: पीएम स्वनिधीमध्ये किती कर्ज मिळते?\n"
            "उत्तर: पहिले कर्ज: 10,000 रुपये. दुसरे: 20,000 (पहिले फेडल्यानंतर). तिसरे: 50,000 (दुसरे फेडल्यानंतर).\n\n"
            "प्रश्न: व्याजदर किती?\n"
            "उत्तर: बँक नियमित व्याज लावते पण सरकार 7% वार्षिक व्याज सवलत देते.\n\n"
            "प्रश्न: गॅरंटी किंवा जामीन लागते का?\n"
            "उत्तर: नाही. स्वनिधी कर्ज गॅरंटी आणि जामीनशिवाय मिळते.\n\n"
            "प्रश्न: कर्ज कित्या दिवसांत फेडायचे?\n"
            "उत्तर: प्रत्येक कर्ज 12 मासिक हप्त्यांत फेडायचे. वेळेवर फेडल्यास पुढचे मोठे कर्ज मिळते.\n\n"
            "प्रश्न: कॅशबॅक म्हणजे काय?\n"
            "उत्तर: डिजिटल पेमेंट (UPI, QR कोड) वापरणाऱ्या विक्रेत्यांना वार्षिक 1,200 रुपयांपर्यंत कॅशबॅक.\n\n"
            "प्रश्न: अर्ज कसे करायचे?\n"
            "उत्तर: pmsvanidhi.mohua.gov.in वर ऑनलाइन किंवा PM स्वनिधी अॅपवरून. CSC केंद्रही मदत करतात.\n\n"
            "प्रश्न: कर्जाची स्थिती कशी तपासायची?\n"
            "उत्तर: pmsvanidhi.mohua.gov.in वर मोबाइल नंबरने लॉगिन करा, किंवा 1800-11-1979 वर कॉल करा."
        ),
        "text_ta": (
            "பிஎம் ஸ்வநிதி பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: பிஎம் ஸ்வநிதியில் எவ்வளவு கடன் கிடைக்கும்?\n"
            "ப: முதல் கடன்: 10,000 ரூபாய். இரண்டாவது: 20,000 (முதல் கடன் திருப்பிய பிறகு). மூன்றாவது: 50,000 (இரண்டாவது திருப்பிய பிறகு).\n\n"
            "கே: வட்டி விகிதம் என்ன?\n"
            "ப: வங்கி வழக்கமான வட்டி வசூலிக்கும் ஆனால் அரசு 7% ஆண்டு வட்டி மானியம் தருகிறது.\n\n"
            "கே: கடன் எத்தனை நாட்களில் திருப்பிக்க வேண்டும்?\n"
            "ப: ஒவ்வொரு கடனும் 12 மாத தவணைகளில் திருப்பிக்க வேண்டும். சரியான நேரத்தில் திருப்பித்தால் அடுத்த பெரிய கடன் கிடைக்கும்.\n\n"
            "கே: கடன் நிலை எப்படி பார்ப்பது?\n"
            "ப: pmsvanidhi.mohua.gov.in இல் மொபைல் எண்ணுடன் லாக்இன் செய்யுங்கள், அல்லது 1800-11-1979 அழைக்கவும்."
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
        "text_mr": (
            "बेटी बचाओ बेटी पढाओ बद्दल वारंवार विचारले जाणारे प्रश्न:\n\n"
            "प्रश्न: ही कोणती आर्थिक योजना आहे का?\n"
            "उत्तर: नाही, ही मुख्यत्वे जागृती मोहीम आहे. थेट पैसे मिळत नाहीत. पण सुकन्या समृद्धी, शिष्यवृत्ती आणि CBSE उडान सारख्या योजनांशी जोडते.\n\n"
            "प्रश्न: या योजनेचे उद्देश काय आहेत?\n"
            "उत्तर: (1) लिंगाधारित निवड आणि कन्या भ्रूणहत्या थांबवणे, (2) मुलींचे अस्तित्व आणि संरक्षण, (3) मुलींचे शिक्षण आणि सहभाग.\n\n"
            "प्रश्न: माझ्या मुलीला काय फायदा?\n"
            "उत्तर: चांगल्या आरोग्य सेवा, शाळेत नावनोंदणी मोहीम, बालविवाह विरोधी जागृती, आणि मुलींसाठी आर्थिक योजनांशी जोडणे.\n\n"
            "प्रश्न: मुलींसाठी हेल्पलाइन?\n"
            "उत्तर: महिला हेल्पलाइन: 181. बाल हेल्पलाइन: 1098.\n\n"
            "प्रश्न: मुलींसाठी कोणत्या आर्थिक योजना आहेत?\n"
            "उत्तर: सुकन्या समृद्धी योजना (बचत), राष्ट्रीय शिष्यवृत्ती पोर्टल (शिक्षण), लाडली लक्ष्मी (राज्य योजना)."
        ),
        "text_ta": (
            "பெண் குழந்தைகளை காப்பாற்றுங்கள் பெண் குழந்தைகளை படிக்க வையுங்கள் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n\n"
            "கே: இது ஒரு நிதி திட்டமா?\n"
            "ப: இல்லை, இது முக்கியமாக விழிப்புணர்வு அபியானம். நேரடியாக பணம் கொடுக்காது. ஆனால் சுகன்யா சம்ரிதி, ஸ்காலர்ஷிப், CBSE உடான் போன்ற திட்டங்களுடன் இணைக்கும்.\n\n"
            "கே: இதன் நோக்கங்கள் என்ன?\n"
            "ப: (1) பாலின அடிப்படையிலான பாலினத் தேர்வைத் தடுப்பது, (2) பெண் குழந்தைகளின் பாதுகாப்பு, (3) பெண்களின் கல்வி மற்றும் பங்கேற்பு.\n\n"
            "கே: என் மகளுக்கு என்ன பயன்?\n"
            "ப: மேம்பட்ட சுகாதார சேவைகள், பள்ளிச் சேர்க்கை அபியானங்கள், குழந்தைத் திருமணத்திற்கு எதிரான விழிப்புணர்வு, பெண்களுக்கான நிதி திட்டங்களுடன் இணைப்பு.\n\n"
            "கே: பெண்கள் பாதுகாப்புக்கு ஹெல்ப்லைன்?\n"
            "ப: பெண்கள் ஹெல்ப்லைன்: 181. குழந்தைகள் ஹெல்ப்லைன்: 1098.\n\n"
            "கே: பெண்களுக்கான நிதி திட்டங்கள் என்ன?\n"
            "ப: சுகன்யா சம்ரிதி யோஜனா (சேமிப்பு), தேசிய ஸ்காலர்ஷிப் போர்ட்டல் (கல்வி), லாட்லி லட்சுமி (மாநில திட்டங்கள்)."
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

        "text_mr": (
            "जननी सुरक्षा योजना (JSY) बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: JSY मध्ये किती पैसे मिळतात?\n"
            "उत्तर: कमी कामगिरी राज्यांमध्ये (UP, बिहार, MP, राजस्थान इ.): ग्रामीण मातांना 1,400 आणि शहरी मातांना 1,000 रुपये. जास्त कामगिरी राज्यांमध्ये: ग्रामीण BPL ला 700, शहरी BPL ला 600 रुपये.\n"
            "\n"
            "प्रश्न: पैसे कधी मिळतात?\n"
            "उत्तर: रुग्णालयात प्रसुतीच्या वेळी किंवा काही दिवसांत बँक खात्यात.\n"
            "\n"
            "प्रश्न: वयाची मर्यादा आहे का?\n"
            "उत्तर: उच्च कामगिरी राज्यांत 19 वर्षे किंवा अधिक. कमी कामगिरी राज्यांत वयाची मर्यादा नाही.\n"
            "\n"
            "प्रश्न: आशा कार्यकर्ती काय करते?\n"
            "उत्तर: नोंदणी, रुग्णालयात नेणे, वाहतूक व्यवस्था, कागदपत्रे आणि पेमेंट. आशाला प्रत्येक प्रसुतीसाठी 600 (ग्रामीण) किंवा 200 (शहरी) रुपये मिळतात.\n"
            "\n"
            "प्रश्न: रुग्णालयाने पैसे मागितले तर?\n"
            "उत्तर: सरकारी रुग्णालयात सर्व काही मोफत. पैसे मागितल्यास रुग्णालय अधीक्षक, CMO कडे तक्रार करा किंवा 1800-180-1104 वर कॉल करा."
        ),
        "text_ta": (
            "ஜனனி சுரக்ஷா யோஜனா (JSY) பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: JSY இல் எவ்வளவு பணம் கிடைக்கும்?\n"
            "ப: குறைந்த செயல்திறன் மாநிலங்களில் (UP, பீகார், MP, ராஜஸ்தான் போன்றவை): கிராமப் பெண்களுக்கு 1,400, நகரப் பெண்களுக்கு 1,000 ரூபாய். உயர் செயல்திறன் மாநிலங்களில்: கிராம BPL க்கு 700, நகர BPL க்கு 600 ரூபாய்.\n"
            "\n"
            "கே: பணம் எப்போது கிடைக்கும்?\n"
            "ப: மருத்துவமனையில் பிரசவ நேரத்தில் அல்லது சில நாட்களில் வங்கிக் கணக்கில்.\n"
            "\n"
            "கே: ஆஷா ஊழியர் என்ன செய்வார்?\n"
            "ப: பதிவு, மருத்துவமனைக்கு அழைத்துச் செல்வது, போக்குவரத்து ஏற்பாடு, ஆவணங்கள் மற்றும் பணம் கிடைப்பதை உறுதி செய்வது. ஆஷாவுக்கு ஒவ்வொரு பிரசவத்திற்கும் 600 (கிராமம்) அல்லது 200 (நகரம்) ரூபாய்.\n"
            "\n"
            "கே: மருத்துவமனை பணம் கேட்டால்?\n"
            "ப: அரசு மருத்துவமனையில் அனைத்தும் இலவசம். பணம் கேட்டால் மருத்துவமனை கண்காணிப்பாளர், CMO விடம் புகார் செய்யுங்கள் அல்லது 1800-180-1104 அழைக்கவும்."
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

        "text_mr": (
            "पीएम गरीब कल्याण अन्न योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: किती मोफत धान्य मिळते?\n"
            "उत्तर: प्रति व्यक्ती दरमहा 5 किलो मोफत धान्य. अंत्योदय (AAY) कुटुंबांना प्रति कुटुंब 35 किलो.\n"
            "\n"
            "प्रश्न: कोणते धान्य मिळते?\n"
            "उत्तर: राज्यानुसार गहू, तांदूळ किंवा भरड धान्य. भारतीय अन्न महामंडळाच्या मानकानुसार गुणवत्ता.\n"
            "\n"
            "प्रश्न: काही पैसे द्यावे लागतात का?\n"
            "उत्तर: नाही, धान्य पूर्णपणे मोफत. रेशन दुकानदाराने पैसे मागणे बेकायदेशीर.\n"
            "\n"
            "प्रश्न: रेशन कार्ड कसे बनवायचे?\n"
            "उत्तर: जिल्हा अन्न व पुरवठा कार्यालयात किंवा राज्य PDS पोर्टलवर ऑनलाइन. आधार, पत्ता पुरावा, उत्पन्न प्रमाणपत्र, कुटुंब तपशील.\n"
            "\n"
            "प्रश्न: दुसऱ्या दुकानातून रेशन घेता येते का?\n"
            "उत्तर: होय. One Nation One Ration Card अंतर्गत भारतातील कोणत्याही रेशन दुकानातून आधारने रेशन घेता येते.\n"
            "\n"
            "प्रश्न: मोफत धान्य कधीपर्यंत मिळेल?\n"
            "उत्तर: NFSA अंतर्गत डिसेंबर 2028 पर्यंत वाढवली.\n"
            "\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: 1967 (अन्न हेल्पलाइन) वर कॉल करा, जिल्हा अन्न अधिकाऱ्याशी भेटा, किंवा राज्य PDS पोर्टलवर ऑनलाइन तक्रार."
        ),
        "text_ta": (
            "பிஎம் கரீப் கல்யாண் அன்ன யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: எவ்வளவு இலவச தானியம் கிடைக்கும்?\n"
            "ப: ஒரு நபருக்கு மாதம் 5 கிலோ இலவச தானியம். அந்த்யோதய (AAY) குடும்பங்களுக்கு குடும்பத்திற்கு 35 கிலோ.\n"
            "\n"
            "கே: என்ன தானியம் கொடுக்கப்படும்?\n"
            "ப: மாநிலத்தைப் பொறுத்து கோதுமை, அரிசி அல்லது கொரத்தானியங்கள்.\n"
            "\n"
            "கே: ஏதாவது பணம் செலுத்த வேண்டுமா?\n"
            "ப: இல்லை, தானியம் முற்றிலும் இலவசம். ரேஷன் கடைக்காரர் பணம் கேட்டால் அது சட்டவிரோதம்.\n"
            "\n"
            "கே: ரேஷன் கார்டு எப்படி பெறுவது?\n"
            "ப: மாவட்ட உணவு வழங்கல் அலுவலகத்தில் அல்லது மாநில PDS போர்ட்டலில் ஆன்லைனில். ஆதார், முகவரி ஆதாரம், வருமானச் சான்றிதழ், குடும்ப விவரங்கள்.\n"
            "\n"
            "கே: வேறு கடையிலிருந்து ரேஷன் வாங்க முடியுமா?\n"
            "ப: ஆம். One Nation One Ration Card திட்டத்தில் இந்தியாவின் எந்த ரேஷன் கடையிலும் ஆதார் மூலம் ரேஷன் வாங்கலாம்.\n"
            "\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: 1967 (உணவு ஹெல்ப்லைன்) அழைக்கவும், மாவட்ட உணவு அதிகாரியை தொடர்பு கொள்ளவும், அல்லது மாநில PDS போர்ட்டலில் புகார் செய்யவும்."
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

        "text_mr": (
            "पीएम जन धन योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: जन धन खाते मोफत आहे का?\n"
            "उत्तर: होय. शून्य शिल्लक खाते, मोफत RuPay डेबिट कार्ड. किमान शिल्लक नाही. उघडण्याचे शुल्क नाही.\n"
            "\n"
            "प्रश्न: जन धन खात्यासोबत कोणते विमा मिळते?\n"
            "उत्तर: RuPay कार्डमधून 2 लाख रुपये अपघाती मृत्यू/अपंगत्व विमा, आणि 30,000 रुपये जीवन विमा (पात्र खात्यांसाठी).\n"
            "\n"
            "प्रश्न: ओव्हरड्राफ्ट सुविधा काय आहे?\n"
            "उत्तर: 6 महिने चांगला खाता इतिहास असल्यास 10,000 रुपयांपर्यंत ओव्हरड्राफ्ट (कर्ज) मिळू शकते. प्रति कुटुंब एक.\n"
            "\n"
            "प्रश्न: सरकारी योजनांचे पैसे जन धन खात्यात येतात का?\n"
            "उत्तर: होय. जन धन खाती DBT (डायरेक्ट बेनिफिट ट्रान्सफर) सक्षम आहेत. सर्व सरकारी सबसिडी आणि पेमेंट्स येऊ शकतात.\n"
            "\n"
            "प्रश्न: आधार कसे लिंक करायचे?\n"
            "उत्तर: बँक शाखेत आधार कार्ड घेऊन जा. छोटा फॉर्म भरा. सरकारी लाभ मिळण्यासाठी हे आवश्यक."
        ),
        "text_ta": (
            "பிஎம் ஜன் தன் யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: ஜன் தன் கணக்கு இலவசமா?\n"
            "ப: ஆம். ஜீரோ பேலன்ஸ் கணக்கு, இலவச RuPay டெபிட் கார்டு. குறைந்தபட்ச இருப்பு தேவையில்லை. திறப்பதற்கு கட்டணம் இல்லை.\n"
            "\n"
            "கே: ஜன் தன் கணக்குடன் என்ன காப்பீடு கிடைக்கும்?\n"
            "ப: RuPay கார்டு மூலம் 2 லட்சம் ரூபாய் விபத்து மரணம்/ஊனம் காப்பீடு, மற்றும் 30,000 ரூபாய் ஆயுள் காப்பீடு (தகுதியான கணக்குகளுக்கு).\n"
            "\n"
            "கே: ஓவர்டிராஃப்ட் வசதி என்ன?\n"
            "ப: 6 மாதம் நல்ல கணக்கு வரலாறு இருந்தால் 10,000 ரூபாய் வரை ஓவர்டிராஃப்ட் (கடன்) கிடைக்கும். குடும்பத்திற்கு ஒன்று.\n"
            "\n"
            "கே: அரசு திட்டப் பணம் ஜன் தன் கணக்கில் வரும?\n"
            "ப: ஆம். ஜன் தன் கணக்குகள் DBT (நேரடி பயன் பரிமாற்றம்) செயல்படுத்தப்பட்டவை. அனைத்து அரசு மானியங்களும் வரும்.\n"
            "\n"
            "கே: ஆதார் எப்படி இணைப்பது?\n"
            "ப: வங்கிக் கிளைக்கு ஆதார் அட்டையுடன் செல்லுங்கள். சிறிய படிவம் நிரப்புங்கள். அரசு நன்மைகள் பெற இது அவசியம்."
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

        "text_mr": (
            "पीएम उज्ज्वला योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: उज्ज्वलामध्ये काय मिळते?\n"
            "उत्तर: मोफत LPG गॅस कनेक्शन, कनेक्शनसाठी 1,600 रुपये, पहिला गॅस रिफिल मोफत आणि मोफत चूल. त्यानंतर बाजार किंवा सबसिडी दराने रिफिल खरेदी करा.\n"
            "\n"
            "प्रश्न: कोण अर्ज करू शकते?\n"
            "उत्तर: BPL कुटुंबे, SC/ST, PMAY लाभार्थी, अंत्योदय, वन/बेट निवासी, अत्यंत मागास वर्गातील प्रौढ महिला (18+).\n"
            "\n"
            "प्रश्न: पुरुषाच्या नावावर कनेक्शन मिळेल का?\n"
            "उत्तर: नाही. LPG कनेक्शन घरातील प्रौढ महिलेच्या नावावरच.\n"
            "\n"
            "प्रश्न: अर्ज कसा करायचा?\n"
            "उत्तर: जवळच्या LPG वितरकाकडे (HP, भारत किंवा इंडेन) आधार, BPL रेशन कार्ड आणि बँक पासबुक घेऊन जा. किंवा pmuy.gov.in वर ऑनलाइन.\n"
            "\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: 1906 (LPG हेल्पलाइन) वर कॉल करा किंवा LPG वितरकाशी संपर्क करा. ऑनलाइन: mylpg.in."
        ),
        "text_ta": (
            "பிஎம் உஜ்வாலா யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: உஜ்வாலாவில் என்ன கிடைக்கும்?\n"
            "ப: இலவச LPG கேஸ் இணைப்பு, இணைப்புக்கு 1,600 ரூபாய், முதல் கேஸ் ரீஃபில் இலவசம், இலவச அடுப்பு. அதன் பிறகு சந்தை அல்லது மானிய விலையில் ரீஃபில் வாங்க வேண்டும்.\n"
            "\n"
            "கே: யார் விண்ணப்பிக்கலாம்?\n"
            "ப: BPL குடும்பங்கள், SC/ST, PMAY பயனாளிகள், அந்த்யோதய, காடு/தீவு மக்கள், மிகவும் பிற்படுத்தப்பட்ட வகுப்பினரின் வயது வந்த பெண்கள் (18+).\n"
            "\n"
            "கே: ஆணின் பெயரில் இணைப்பு கிடைக்குமா?\n"
            "ப: இல்லை. LPG இணைப்பு வீட்டின் வயது வந்த பெண்ணின் பெயரில் மட்டுமே.\n"
            "\n"
            "கே: எப்படி விண்ணப்பிப்பது?\n"
            "ப: அருகிலுள்ள LPG விநியோகஸ்தரிடம் (HP, பாரத், இண்டேன்) ஆதார், BPL ரேஷன் கார்டு, வங்கி பாஸ்புக் எடுத்துச் செல்லுங்கள். அல்லது pmuy.gov.in இல் ஆன்லைனில்.\n"
            "\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: 1906 (LPG ஹெல்ப்லைன்) அழைக்கவும் அல்லது LPG விநியோகஸ்தரை தொடர்பு கொள்ளவும். ஆன்லைன்: mylpg.in."
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

        "text_mr": (
            "राष्ट्रीय शिष्यवृत्ती पोर्टल बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: NSP वर कोणत्या शिष्यवृत्त्या आहेत?\n"
            "उत्तर: प्री-मॅट्रिक, पोस्ट-मॅट्रिक, टॉप-क्लास, मेरिट-कम-मीन्स, आणि SC, ST, OBC, अल्पसंख्याक, दिव्यांग विद्यार्थ्यांसाठी विशेष शिष्यवृत्त्या.\n"
            "\n"
            "प्रश्न: किती पैसे मिळतात?\n"
            "उत्तर: शिष्यवृत्तीनुसार 1,500 ते 20,000+ रुपये वार्षिक. काहींमध्ये पूर्ण ट्यूशन फी, हॉस्टेल आणि मेंटेनन्स भत्ता.\n"
            "\n"
            "प्रश्न: NSP वर अर्ज कसा करायचा?\n"
            "उत्तर: scholarships.gov.in वर नोंदणी > OTR बनवा > लॉगिन > शिष्यवृत्ती निवडा > फॉर्म भरा > कागदपत्रे अपलोड > सबमिट. संस्थेला सत्यापित करावे लागेल.\n"
            "\n"
            "प्रश्न: शिष्यवृत्तीचे पैसे कधी मिळतात?\n"
            "उत्तर: संस्था, राज्य आणि केंद्र स्तरावर सत्यापनानंतर. साधारणतः अर्जानंतर 3-6 महिने. DBT ने थेट बँक खात्यात.\n"
            "\n"
            "प्रश्न: एकाच वेळी अनेक शिष्यवृत्त्या घेता येतात का?\n"
            "उत्तर: साधारणतः नाही. एक केंद्रीय आणि एक राज्य शिष्यवृत्ती घेता येते. दोन केंद्रीय एकत्र नाही."
        ),
        "text_ta": (
            "தேசிய உதவித்தொகை போர்ட்டல் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: NSP இல் என்ன உதவித்தொகைகள் உள்ளன?\n"
            "ப: ப்ரீ-மெட்ரிக், போஸ்ட்-மெட்ரிக், டாப்-கிளாஸ், மெரிட்-கம்-மீன்ஸ், SC, ST, OBC, சிறுபான்மையினர், மாற்றுத்திறனாளி மாணவர்களுக்கான சிறப்பு உதவித்தொகைகள்.\n"
            "\n"
            "கே: எவ்வளவு பணம் கிடைக்கும்?\n"
            "ப: உதவித்தொகையைப் பொறுத்து ஆண்டுக்கு 1,500 முதல் 20,000+ ரூபாய். சிலவற்றில் முழு கல்விக் கட்டணம், விடுதி, பராமரிப்புக் கொடுப்பனவு.\n"
            "\n"
            "கே: NSP இல் எப்படி விண்ணப்பிப்பது?\n"
            "ப: scholarships.gov.in இல் பதிவு > OTR உருவாக்கு > உள்நுழை > உதவித்தொகை தேர்வு > படிவம் நிரப்பு > ஆவணங்கள் பதிவேற்றம் > சமர்ப்பி. கல்வி நிறுவனம் சரிபார்க்க வேண்டும்.\n"
            "\n"
            "கே: பணம் எப்போது கிடைக்கும்?\n"
            "ப: நிறுவனம், மாநிலம், மத்திய நிலையில் சரிபார்ப்புக்குப் பிறகு. பொதுவாக விண்ணப்பித்த 3-6 மாதங்களில். DBT மூலம் நேரடியாக வங்கிக் கணக்கில்.\n"
            "\n"
            "கே: ஒரே நேரத்தில் பல உதவித்தொகைகள் பெற முடியுமா?\n"
            "ப: பொதுவாக இல்லை. ஒரு மத்திய மற்றும் ஒரு மாநில உதவித்தொகை பெறலாம். இரண்டு மத்திய உதவித்தொகைகள் ஒரே நேரத்தில் முடியாது."
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

        "text_mr": (
            "मृदा आरोग्य कार्ड योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: कार्डमध्ये काय माहिती मिळते?\n"
            "उत्तर: 12 मापदंडांची स्थिती: pH, विद्युत वाहकता, सेंद्रिय कार्बन, नायट्रोजन, फॉस्फरस, पोटॅशियम, सल्फर, झिंक, लोह, तांबे, मँगनीज, बोरॉन. कोणते खत किती वापरायचे हेही सांगते.\n"
            "\n"
            "प्रश्न: कार्ड मोफत आहे का?\n"
            "उत्तर: होय, पूर्णपणे मोफत. माती तपासणी किंवा कार्ड बनवण्याचे कोणतेही शुल्क नाही.\n"
            "\n"
            "प्रश्न: कार्ड किती वेळा मिळते?\n"
            "उत्तर: दर 2 वर्षांनी एकदा.\n"
            "\n"
            "प्रश्न: कार्ड कसे मिळवायचे?\n"
            "उत्तर: कृषी विज्ञान केंद्र, स्थानिक कृषी अधिकारी यांच्याशी संपर्क करा, किंवा soilhealth.dac.gov.in वर नोंदणी करा.\n"
            "\n"
            "प्रश्न: कार्डाच्या शिफारशी पाळल्यास खरोखर फसल सुधारते का?\n"
            "उत्तर: होय. अभ्यास दर्शवतात की शिफारशी पाळणारे शेतकरी खतावर 10-15% बचत करतात आणि उत्पादन 10-20% वाढते."
        ),
        "text_ta": (
            "மண் நல அட்டை திட்டம் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: அட்டையில் என்ன தகவல் கிடைக்கும்?\n"
            "ப: 12 அளவுகளின் நிலை: pH, மின் கடத்தல், கரிமக் கார்பன், நைட்ரஜன், பாஸ்பரஸ், பொட்டாசியம், சல்ஃபர், ஜிங்க், இரும்பு, செம்பு, மாங்கனீஸ், போரான். எந்த உரம் எவ்வளவு பயன்படுத்த வேண்டும் என்றும் பரிந்துரைக்கும்.\n"
            "\n"
            "கே: அட்டை இலவசமா?\n"
            "ப: ஆம், முற்றிலும் இலவசம். மண் பரிசோதனை அல்லது அட்டை வழங்குவதற்கு கட்டணம் இல்லை.\n"
            "\n"
            "கே: அட்டை எப்படி பெறுவது?\n"
            "ப: கிருஷி விக்யான் கேந்திரா, உள்ளூர் வேளாண் அதிகாரியை தொடர்பு கொள்ளுங்கள், அல்லது soilhealth.dac.gov.in இல் பதிவு செய்யுங்கள்.\n"
            "\n"
            "கே: அட்டையின் பரிந்துரைகளைப் பின்பற்றினால் உண்மையிலேயே பயிர் மேம்படுமா?\n"
            "ப: ஆம். ஆய்வுகள் காட்டுகின்றன - பரிந்துரைகளைப் பின்பற்றும் விவசாயிகள் உரத்தில் 10-15% சேமிக்கிறார்கள், விளைச்சல் 10-20% அதிகரிக்கும்."
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

        "text_mr": (
            "पीएम पोषण (मध्याह्न भोजन) बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: मध्याह्न भोजन कोणाला मिळते?\n"
            "उत्तर: सरकारी, सरकारी अनुदानित आणि स्थानिक संस्थांच्या शाळांमध्ये इयत्ता 1 ते 8 च्या सर्व मुलांना.\n"
            "\n"
            "प्रश्न: काय जेवण मिळते?\n"
            "उत्तर: भात/गहू, डाळ, भाजी आणि तेलाने बनवलेले शिजवलेले जेवण. राज्यानुसार अंडी, फळे किंवा दूधही.\n"
            "\n"
            "प्रश्न: किती कॅलरी मिळतात?\n"
            "उत्तर: प्राथमिक (इयत्ता 1-5): 450 कॅलरी आणि 12 ग्रॅम प्रोटिन. उच्च प्राथमिक (इयत्ता 6-8): 700 कॅलरी आणि 20 ग्रॅम प्रोटिन.\n"
            "\n"
            "प्रश्न: अन्नाची गुणवत्ता खराब असेल तर?\n"
            "उत्तर: शाळेचे मुख्याध्यापक, खंड शिक्षणाधिकारी यांच्याकडे तक्रार करा किंवा 1800-180-5727 वर कॉल करा."
        ),
        "text_ta": (
            "பிஎம் போஷன் (மதிய உணவு) பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: மதிய உணவு யாருக்கு கிடைக்கும்?\n"
            "ப: அரசு, அரசு உதவி பெறும், உள்ளாட்சி அமைப்பு பள்ளிகளில் வகுப்பு 1 முதல் 8 வரை படிக்கும் அனைத்து குழந்தைகளுக்கும்.\n"
            "\n"
            "கே: என்ன உணவு கொடுக்கப்படும்?\n"
            "ப: அரிசி/கோதுமை, பருப்பு, காய்கறி, எண்ணெய் கொண்டு சமைக்கப்பட்ட உணவு. மாநிலத்தைப் பொறுத்து முட்டை, பழம் அல்லது பால்.\n"
            "\n"
            "கே: எவ்வளவு கலோரி கிடைக்கும்?\n"
            "ப: தொடக்கநிலை (வகுப்பு 1-5): 450 கலோரி, 12 கிராம் புரதம். மேல்நிலை (வகுப்பு 6-8): 700 கலோரி, 20 கிராம் புரதம்.\n"
            "\n"
            "கே: உணவு தரம் மோசமாக இருந்தால்?\n"
            "ப: பள்ளி தலைமையாசிரியர், வட்டக் கல்வி அதிகாரியிடம் புகார் செய்யுங்கள் அல்லது 1800-180-5727 அழைக்கவும்."
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

        "text_mr": (
            "महिला सन्मान बचत प्रमाणपत्र बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: व्याजदर किती आहे?\n"
            "उत्तर: 7.5% वार्षिक, तिमाही चक्रवाढ. बहुतेक फिक्स्ड डिपॉझिटपेक्षा जास्त.\n"
            "\n"
            "प्रश्न: किमान आणि कमाल ठेव किती?\n"
            "उत्तर: किमान 1,000 रुपये, कमाल 2 लाख रुपये.\n"
            "\n"
            "प्रश्न: खाते कधी परिपक्व होते?\n"
            "उत्तर: उघडल्यापासून 2 वर्षांनी. परिपक्वतेवर पूर्ण रक्कम आणि व्याज मिळते.\n"
            "\n"
            "प्रश्न: 2 वर्षांपूर्वी पैसे काढता येतात का?\n"
            "उत्तर: होय. 1 वर्षानंतर 40% पर्यंत आंशिक काढता येते.\n"
            "\n"
            "प्रश्न: कुठे खाते उघडायचे?\n"
            "उत्तर: कोणत्याही पोस्ट ऑफिस किंवा अधिकृत बँक शाखेत.\n"
            "\n"
            "प्रश्न: पुरुष हे खाते उघडू शकतो का?\n"
            "उत्तर: खाते महिला किंवा मुलीच्या नावावर असावे. पुरुष अल्पवयीन मुलीचा पालक म्हणून उघडू शकतो."
        ),
        "text_ta": (
            "மகிளா சம்மான் சேமிப்புச் சான்றிதழ் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: வட்டி விகிதம் என்ன?\n"
            "ப: ஆண்டுக்கு 7.5%, காலாண்டு கூட்டு வட்டி. பெரும்பாலான ஃபிக்ஸட் டெபாசிட்களை விட அதிகம்.\n"
            "\n"
            "கே: குறைந்தபட்ச மற்றும் அதிகபட்ச வைப்புத்தொகை?\n"
            "ப: குறைந்தபட்சம் 1,000 ரூபாய், அதிகபட்சம் 2 லட்சம் ரூபாய்.\n"
            "\n"
            "கே: கணக்கு எப்போது முதிர்வு அடையும்?\n"
            "ப: திறந்த நாளிலிருந்து 2 ஆண்டுகளுக்குப் பிறகு. முதிர்வில் முழு தொகையும் வட்டியும் கிடைக்கும்.\n"
            "\n"
            "கே: 2 ஆண்டுகளுக்கு முன் பணம் எடுக்க முடியுமா?\n"
            "ப: ஆம். 1 ஆண்டுக்குப் பிறகு 40% வரை பகுதி எடுப்பு அனுமதிக்கப்படுகிறது.\n"
            "\n"
            "கே: எங்கு கணக்கு திறப்பது?\n"
            "ப: எந்த தபால் நிலையத்திலும் அல்லது அங்கீகரிக்கப்பட்ட வங்கிக் கிளையிலும்.\n"
            "\n"
            "கே: ஆண் இந்தக் கணக்கைத் திறக்க முடியுமா?\n"
            "ப: கணக்கு பெண் அல்லது பெண் குழந்தையின் பெயரில் இருக்க வேண்டும். ஆண் சிறுமியின் பாதுகாவலராக திறக்கலாம்."
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

        "text_mr": (
            "पीएम कौशल्य विकास योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: PMKVY प्रशिक्षण मोफत आहे का?\n"
            "उत्तर: होय. प्रशिक्षण, मूल्यमापन आणि प्रमाणन पूर्णपणे मोफत. प्रशिक्षणादरम्यान लहान भत्ताही मिळतो.\n"
            "\n"
            "प्रश्न: कोणते कोर्स उपलब्ध आहेत?\n"
            "उत्तर: IT, रिटेल, ब्यूटी, आरोग्य, ऑटोमोटिव्ह, बांधकाम, इलेक्ट्रीशियन, प्लंबर, वेल्डिंग, शिवणकाम, फूड प्रोसेसिंग सह 300+ कोर्स.\n"
            "\n"
            "प्रश्न: प्रशिक्षणानंतर नोकरी मिळेल का?\n"
            "उत्तर: PMKVY चे लक्ष्य 70% प्लेसमेंट. केंद्रे प्लेसमेंटमध्ये मदत करतात. पण नोकरीची हमी नाही.\n"
            "\n"
            "प्रश्न: जवळचे प्रशिक्षण केंद्र कसे शोधायचे?\n"
            "उत्तर: pmkvyofficial.org > Find a Training Centre > राज्य, जिल्हा आणि क्षेत्र निवडा.\n"
            "\n"
            "प्रश्न: प्रमाणपत्र मिळते का?\n"
            "उत्तर: होय. NSQF अनुरूप सेक्टर स्किल काउंसिलचे प्रमाणपत्र. उद्योगाने मान्यताप्राप्त."
        ),
        "text_ta": (
            "பிஎம் கௌசல் விகாஸ் யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: PMKVY பயிற்சி இலவசமா?\n"
            "ப: ஆம். பயிற்சி, மதிப்பீடு, சான்றிதழ் முற்றிலும் இலவசம். பயிற்சியின் போது சிறிய கொடுப்பனவும் கிடைக்கும்.\n"
            "\n"
            "கே: என்ன படிப்புகள் உள்ளன?\n"
            "ப: IT, சில்லறை, அழகுக்கலை, சுகாதாரம், வாகனம், கட்டுமானம், எலக்ட்ரீஷியன், பிளம்பர், வெல்டிங், தையல், உணவு பதப்படுத்தல் உள்ளிட்ட 300+ படிப்புகள்.\n"
            "\n"
            "கே: பயிற்சிக்குப் பிறகு வேலை கிடைக்குமா?\n"
            "ப: PMKVY இன் இலக்கு 70% வேலைவாய்ப்பு. மையங்கள் வேலைவாய்ப்பில் உதவுகின்றன. ஆனால் வேலை உத்தரவாதம் இல்லை.\n"
            "\n"
            "கே: அருகிலுள்ள பயிற்சி மையம் எப்படி கண்டுபிடிப்பது?\n"
            "ப: pmkvyofficial.org > Find a Training Centre > மாநிலம், மாவட்டம், துறை தேர்வு செய்யுங்கள்.\n"
            "\n"
            "கே: சான்றிதழ் கிடைக்குமா?\n"
            "ப: ஆம். NSQF இணக்கமான செக்டார் ஸ்கில் கவுன்சில் சான்றிதழ். தொழில்துறையால் அங்கீகரிக்கப்பட்டது."
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

        "text_mr": (
            "पीएम सुरक्षा बीमा योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: PMSBY ची किंमत किती?\n"
            "उत्तर: फक्त 20 रुपये वार्षिक (2 रुपये/महिन्यापेक्षा कमी). बँक खात्यातून वर्षातून एकदा ऑटो-डेबिट.\n"
            "\n"
            "प्रश्न: PMSBY मध्ये काय कव्हर होते?\n"
            "उत्तर: अपघाती मृत्यू: 2 लाख. पूर्ण कायम अपंगत्व: 2 लाख. आंशिक कायम अपंगत्व: 1 लाख. फक्त अपघात, नैसर्गिक मृत्यू कव्हर नाही.\n"
            "\n"
            "प्रश्न: विमा दावा कसा करायचा?\n"
            "उत्तर: अपघात झाल्यास बँकेला कळवा. दावा फॉर्म, FIR, रुग्णालय रेकॉर्ड, अपंगत्व प्रमाणपत्र आणि नॉमिनीची बँक माहिती सादर करा.\n"
            "\n"
            "प्रश्न: PMSBY नैसर्गिक मृत्यू कव्हर करते का?\n"
            "उत्तर: नाही. PMSBY फक्त अपघात कव्हर करते. जीवन विमा (कोणत्याही कारणाने) साठी PMJJBY घ्या.\n"
            "\n"
            "प्रश्न: वय मर्यादा काय?\n"
            "उत्तर: 18 ते 70 वर्षे."
        ),
        "text_ta": (
            "பிஎம் சுரக்ஷா பீமா யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: PMSBY எவ்வளவு செலவாகும்?\n"
            "ப: ஆண்டுக்கு வெறும் 20 ரூபாய் (மாதம் 2 ரூபாய்க்கும் குறைவு). வங்கிக் கணக்கிலிருந்து ஆண்டுக்கு ஒருமுறை ஆட்டோ-டெபிட்.\n"
            "\n"
            "கே: PMSBY என்ன கவர் செய்யும்?\n"
            "ப: விபத்து மரணம்: 2 லட்சம். மொத்த நிரந்தர ஊனம்: 2 லட்சம். பகுதி நிரந்தர ஊனம்: 1 லட்சம். விபத்து மட்டுமே, இயற்கை மரணம் கவர் இல்லை.\n"
            "\n"
            "கே: காப்பீடு கோரிக்கை எப்படி செய்வது?\n"
            "ப: விபத்து ஏற்பட்டால் வங்கிக்கு தெரிவிக்கவும். கோரிக்கை படிவம், FIR, மருத்துவமனை பதிவுகள், ஊனச் சான்றிதழ், நாமினியின் வங்கி விவரங்கள் சமர்ப்பிக்கவும்.\n"
            "\n"
            "கே: PMSBY இயற்கை மரணத்தை கவர் செய்யுமா?\n"
            "ப: இல்லை. PMSBY விபத்து மட்டுமே கவர் செய்யும். ஆயுள் காப்பீடுக்கு (எந்த காரணமானாலும்) PMJJBY எடுங்கள்.\n"
            "\n"
            "கே: வயது வரம்பு என்ன?\n"
            "ப: 18 முதல் 70 வயது."
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

        "text_mr": (
            "पीएम जीवन ज्योती बीमा योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: PMJJBY ची किंमत किती?\n"
            "उत्तर: 436 रुपये वार्षिक. बँक खात्यातून वर्षातून एकदा ऑटो-डेबिट.\n"
            "\n"
            "प्रश्न: PMJJBY मध्ये काय कव्हर होते?\n"
            "उत्तर: विमाधारकाच्या कोणत्याही कारणाने मृत्यू झाल्यास नॉमिनीला 2 लाख रुपये - अपघात, नैसर्गिक मृत्यू, आजार, कोणतेही कारण.\n"
            "\n"
            "प्रश्न: PMJJBY आणि PMSBY मध्ये काय फरक?\n"
            "उत्तर: PMJJBY कोणत्याही कारणाने मृत्यू कव्हर करते (436/वर्ष, 2 लाख). PMSBY फक्त अपघात (20/वर्ष, 2 लाख). दोन्ही घेता येतात.\n"
            "\n"
            "प्रश्न: दोन्ही PMJJBY आणि PMSBY घेता येतात का?\n"
            "उत्तर: होय. दोन्ही मिळून फक्त 456 रुपये/वर्षात 4 लाखांपर्यंत कव्हर.\n"
            "\n"
            "प्रश्न: वैद्यकीय तपासणी लागते का?\n"
            "उत्तर: नाही. कोणतीही वैद्यकीय तपासणी किंवा आरोग्य घोषणा नाही. नावनोंदणीवेळी साधी स्व-घोषणा."
        ),
        "text_ta": (
            "பிஎம் ஜீவன் ஜோதி பீமா யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: PMJJBY எவ்வளவு செலவாகும்?\n"
            "ப: ஆண்டுக்கு 436 ரூபாய். வங்கிக் கணக்கிலிருந்து ஆண்டுக்கு ஒருமுறை ஆட்டோ-டெபிட்.\n"
            "\n"
            "கே: PMJJBY என்ன கவர் செய்யும்?\n"
            "ப: காப்பீடு செய்யப்பட்டவரின் எந்த காரணத்தாலும் மரணம் ஏற்பட்டால் நாமினிக்கு 2 லட்சம் ரூபாய் - விபத்து, இயற்கை மரணம், நோய், எந்த காரணமும்.\n"
            "\n"
            "கே: PMJJBY மற்றும் PMSBY வேறுபாடு என்ன?\n"
            "ப: PMJJBY எந்த காரணத்தாலும் மரணம் கவர் (436/வருடம், 2 லட்சம்). PMSBY விபத்து மட்டும் (20/வருடம், 2 லட்சம்). இரண்டும் எடுக்கலாம்.\n"
            "\n"
            "கே: இரண்டும் எடுக்கலாமா?\n"
            "ப: ஆம். இரண்டும் சேர்ந்து ஆண்டுக்கு 456 ரூபாயில் 4 லட்சம் கவர்.\n"
            "\n"
            "கே: மருத்துவ பரிசோதனை தேவையா?\n"
            "ப: இல்லை. மருத்துவ பரிசோதனை அல்லது ஆரோக்கிய அறிவிப்பு தேவையில்லை. பதிவின் போது எளிய சுய அறிவிப்பு."
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

        "text_mr": (
            "स्टँड अप इंडिया बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: किती कर्ज मिळते?\n"
            "उत्तर: उत्पादन, सेवा किंवा व्यापारात नवीन उद्योग सुरू करण्यासाठी 10 लाख ते 1 कोटी रुपये.\n"
            "\n"
            "प्रश्न: कोण पात्र आहे?\n"
            "उत्तर: 18+ वयाचे SC/ST आणि/किंवा महिला उद्योजक जे पहिल्यांदा नवीन उद्योग सुरू करत आहेत.\n"
            "\n"
            "प्रश्न: परतफेड कालावधी किती?\n"
            "उत्तर: 7 वर्षांपर्यंत, 18 महिन्यांपर्यंतच्या मुदतमाफीसह.\n"
            "\n"
            "प्रश्न: कुठे अर्ज करायचा?\n"
            "उत्तर: standupmitra.in वर नोंदणी करा, किंवा कोणत्याही बँक शाखेत थेट. प्रत्येक बँक शाखेला किमान एक SC/ST आणि एक महिलेला कर्ज द्यायलाच हवे.\n"
            "\n"
            "प्रश्न: जुन्या व्यवसायासाठी कर्ज मिळेल का?\n"
            "उत्तर: नाही. फक्त नव्या उद्योगासाठी. जुन्या व्यवसाय विस्तारासाठी मुद्रा किंवा इतर योजनांमध्ये अर्ज करा."
        ),
        "text_ta": (
            "ஸ்டாண்ட் அப் இந்தியா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: எவ்வளவு கடன் கிடைக்கும்?\n"
            "ப: உற்பத்தி, சேவை அல்லது வர்த்தகத்தில் புதிய நிறுவனம் தொடங்க 10 லட்சம் முதல் 1 கோடி ரூபாய்.\n"
            "\n"
            "கே: யார் தகுதியானவர்?\n"
            "ப: 18+ வயது SC/ST மற்றும்/அல்லது பெண் தொழில்முனைவோர் முதல் முறையாக புதிய நிறுவனம் தொடங்குபவர்கள்.\n"
            "\n"
            "கே: திருப்பிச் செலுத்தும் காலம்?\n"
            "ப: 7 ஆண்டுகள் வரை, 18 மாதங்கள் வரை அவகாசக் காலத்துடன்.\n"
            "\n"
            "கே: எங்கு விண்ணப்பிப்பது?\n"
            "ப: standupmitra.in இல் பதிவு செய்யுங்கள், அல்லது எந்த வங்கிக் கிளையிலும் நேரடியாக. ஒவ்வொரு வங்கிக் கிளையும் குறைந்தது ஒரு SC/ST மற்றும் ஒரு பெண்ணுக்கு கடன் கொடுக்க வேண்டும்.\n"
            "\n"
            "கே: ஏற்கனவே உள்ள தொழிலுக்கு கடன் கிடைக்குமா?\n"
            "ப: இல்லை. புதிய நிறுவனங்களுக்கு மட்டுமே. ஏற்கனவே உள்ள தொழில் விரிவாக்கத்திற்கு முத்ரா அல்லது பிற திட்டங்களில் விண்ணப்பிக்கவும்."
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

        "text_mr": (
            "पीएम मातृ वंदना योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: किती पैसे मिळतात?\n"
            "उत्तर: पहिले मूल: 3 हप्त्यांत 5,000 रुपये. दुसरे मूल (मुलगी): 2 हप्त्यांत 6,000 रुपये. रुग्णालयात जन्म झाल्यास जननी सुरक्षा योजनेतून 1,000 रुपये अतिरिक्त.\n"
            "\n"
            "प्रश्न: नोंदणी कुठे करायची?\n"
            "उत्तर: जवळच्या अंगणवाडी केंद्रात किंवा सरकारी आरोग्य केंद्रात. आशा आणि अंगणवाडी कार्यकर्ती मदत करतील.\n"
            "\n"
            "प्रश्न: सर्व गर्भधारणांसाठी मिळते का?\n"
            "उत्तर: पहिले मूल: सर्वांसाठी. दुसऱ्या मुलाचा लाभ फक्त मुलगी असल्यासच. तिसऱ्या किंवा पुढील गर्भधारणांसाठी नाही.\n"
            "\n"
            "प्रश्न: पेमेंट स्थिती कशी तपासायची?\n"
            "उत्तर: अंगणवाडी कार्यकर्तीला विचारा, जिल्हा महिला व बाल विकास अधिकाऱ्याशी संपर्क करा, किंवा 181 वर कॉल करा."
        ),
        "text_ta": (
            "பிஎம் மாத்ரு வந்தனா யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: எவ்வளவு பணம் கிடைக்கும்?\n"
            "ப: முதல் குழந்தை: 3 தவணைகளில் 5,000 ரூபாய். இரண்டாவது குழந்தை (பெண்): 2 தவணைகளில் 6,000 ரூபாய். மருத்துவமனையில் பிறந்தால் ஜனனி சுரக்ஷா யோஜனாவிலிருந்து 1,000 ரூபாய் கூடுதல்.\n"
            "\n"
            "கே: எங்கு பதிவு செய்வது?\n"
            "ப: அருகிலுள்ள அங்கன்வாடி மையம் அல்லது அரசு சுகாதார நிலையத்தில். ஆஷா மற்றும் அங்கன்வாடி ஊழியர் உதவுவார்கள்.\n"
            "\n"
            "கே: எல்லா கர்ப்பங்களுக்கும் கிடைக்குமா?\n"
            "ப: முதல் குழந்தை: அனைவருக்கும். இரண்டாவது குழந்தை பயன் பெண் குழந்தையாக இருந்தால் மட்டுமே. மூன்றாவது அல்லது அதற்கு மேல் இல்லை.\n"
            "\n"
            "கே: பணம் வந்ததா என்று எப்படி பார்ப்பது?\n"
            "ப: அங்கன்வாடி ஊழியரிடம் கேளுங்கள், மாவட்ட பெண்கள் மற்றும் குழந்தைகள் மேம்பாட்டு அதிகாரியை தொடர்பு கொள்ளுங்கள், அல்லது 181 அழைக்கவும்."
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

        "text_mr": (
            "राष्ट्रीय कुटुंब लाभ योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: कुटुंबाला किती पैसे मिळतात?\n"
            "उत्तर: BPL कुटुंबातील जिवंत सदस्यांना 20,000 रुपये एकरकमी. काही राज्ये अधिक देतात - तुमच्या राज्याशी तपासा.\n"
            "\n"
            "प्रश्न: मृत व्यक्तीची वय मर्यादा काय?\n"
            "उत्तर: मुख्य कमावत्या व्यक्तीचे वय 18-59 वर्षे असावे. 60 किंवा अधिक वयावर ही योजना लागू नाही.\n"
            "\n"
            "प्रश्न: मृत्यूचे कारण महत्त्वाचे आहे का?\n"
            "उत्तर: नाही. कोणत्याही कारणाने मृत्यू - नैसर्गिक, अपघात, आजार, कोणतेही कारण.\n"
            "\n"
            "प्रश्न: अर्ज कसा करायचा?\n"
            "उत्तर: जिल्हा समाज कल्याण कार्यालयात मृत्यू प्रमाणपत्र, BPL कार्ड, आधार, कुटुंब तपशील आणि बँक पासबुक घेऊन जा.\n"
            "\n"
            "प्रश्न: पैसे कधी मिळतात?\n"
            "उत्तर: नियमानुसार अर्जानंतर 4 आठवड्यांत. प्रत्यक्षात 1-3 महिने लागू शकतात.\n"
            "\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: जिल्हा समाज कल्याण अधिकारी, 1800-111-555 वर, किंवा nsap.nic.in वर ऑनलाइन तक्रार करा."
        ),
        "text_ta": (
            "தேசிய குடும்ப நலத் திட்டம் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: குடும்பத்திற்கு எவ்வளவு பணம் கிடைக்கும்?\n"
            "ப: BPL குடும்பத்தின் உயிருள்ள உறுப்பினர்களுக்கு 20,000 ரூபாய் ஒரே தொகையாக. சில மாநிலங்கள் அதிகம் கொடுக்கும் - உங்கள் மாநிலத்தில் சரிபார்க்கவும்.\n"
            "\n"
            "கே: இறந்தவரின் வயது வரம்பு என்ன?\n"
            "ப: முக்கிய வருமானம் ஈட்டுபவரின் வயது 18-59 ஆக இருக்க வேண்டும். 60 வயதுக்கு மேல் இந்தத் திட்டம் பொருந்தாது.\n"
            "\n"
            "கே: மரணக் காரணம் முக்கியமா?\n"
            "ப: இல்லை. எந்த காரணத்தாலும் மரணம் - இயற்கை, விபத்து, நோய், எதுவானாலும்.\n"
            "\n"
            "கே: எப்படி விண்ணப்பிப்பது?\n"
            "ப: மாவட்ட சமூக நலன் அலுவலகத்தில் இறப்புச் சான்றிதழ், BPL அட்டை, ஆதார், குடும்ப விவரங்கள், வங்கி பாஸ்புக் எடுத்துச் செல்லுங்கள்.\n"
            "\n"
            "கே: பணம் எப்போது கிடைக்கும்?\n"
            "ப: விதிகளின்படி விண்ணப்பித்த 4 வாரங்களுக்குள். உண்மையில் 1-3 மாதங்கள் ஆகலாம்.\n"
            "\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: மாவட்ட சமூக நல அதிகாரியிடம், 1800-111-555 இல், அல்லது nsap.nic.in இல் ஆன்லைன் புகார் செய்யவும்."
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

        "text_mr": (
            "समग्र शिक्षा अभियान बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: विद्यार्थ्यांना काय मिळते?\n"
            "उत्तर: मोफत पुस्तके, गणवेश (600 रुपये/मूल/वर्ष), दिव्यांग मुलांसाठी वाहतूक भत्ता (3,000/वर्ष), आणि शाळा अनुदान.\n"
            "\n"
            "प्रश्न: खाजगी शाळेच्या विद्यार्थ्यांना मिळते का?\n"
            "उत्तर: नाही. फक्त सरकारी, सरकारी अनुदानित आणि स्थानिक संस्थांच्या शाळांमधील विद्यार्थ्यांना.\n"
            "\n"
            "प्रश्न: मुलींच्या शिक्षणासाठी काय आहे?\n"
            "उत्तर: कस्तुरबा गांधी बालिका विद्यालये (निवासी), आत्मरक्षण प्रशिक्षण, स्वतंत्र शौचालये, मासिक पाळी स्वच्छता सहाय्य.\n"
            "\n"
            "प्रश्न: लाभ कसे मिळतात?\n"
            "उत्तर: अर्जाची गरज नाही. शाळांमधून स्वयंचलित. मुख्याध्यापक किंवा जिल्हा शिक्षण कार्यालयाशी बोला."
        ),
        "text_ta": (
            "சமக்ர சிக்ஷா அபியான் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: மாணவர்களுக்கு என்ன கிடைக்கும்?\n"
            "ப: இலவச புத்தகங்கள், சீருடை (600 ரூபாய்/குழந்தை/வருடம்), மாற்றுத்திறனாளி குழந்தைகளுக்கு போக்குவரத்து கொடுப்பனவு (3,000/வருடம்), பள்ளி மானியம்.\n"
            "\n"
            "கே: தனியார் பள்ளி மாணவர்களுக்கு கிடைக்குமா?\n"
            "ப: இல்லை. அரசு, அரசு உதவி பெறும், உள்ளாட்சி அமைப்பு பள்ளி மாணவர்களுக்கு மட்டுமே.\n"
            "\n"
            "கே: பெண்கள் கல்விக்கு என்ன உள்ளது?\n"
            "ப: கஸ்தூர்பா காந்தி பாலிகா வித்யாலயங்கள் (விடுதி), சுயரக்ஷணை பயிற்சி, தனி கழிப்பறைகள், மாதவிடாய் சுகாதார உதவி.\n"
            "\n"
            "கே: பயன்கள் எப்படி கிடைக்கும்?\n"
            "ப: விண்ணப்பம் தேவையில்லை. பள்ளிகள் வழியாக தானாக வரும். தலைமையாசிரியர் அல்லது மாவட்ட கல்வி அலுவலகத்தில் பேசுங்கள்."
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

        "text_mr": (
            "राष्ट्रीय बाल स्वास्थ्य कार्यक्रम (RBSK) बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: RBSK मध्ये कोणत्या गोष्टींची तपासणी होते?\n"
            "उत्तर: 4D: (1) जन्मजात दोष (फाटलेले ओठ, क्लब फूट, हृदय दोष), (2) आजार (त्वचा, कान, डोळे, दात, अॅनिमिया), (3) कमतरता (कुपोषण, व्हिटॅमिन D, लोह), (4) विकासात विलंब (शिकण्यात अडचण, बोलण्यात विलंब).\n"
            "\n"
            "प्रश्न: RBSK उपचार मोफत आहे का?\n"
            "उत्तर: होय. तपासणी, रेफरल आणि उपचार सर्व सरकारी रुग्णालयांत मोफत. जन्मजात दोषांची मोफत शस्त्रक्रियाही.\n"
            "\n"
            "प्रश्न: तपासणी कुठे होते?\n"
            "उत्तर: सरकारी शाळा आणि अंगणवाडी केंद्रांमध्ये. RBSK मोबाइल आरोग्य पथके नियमित भेट देतात.\n"
            "\n"
            "प्रश्न: वय मर्यादा काय?\n"
            "उत्तर: जन्मापासून 18 वर्षांपर्यंत.\n"
            "\n"
            "प्रश्न: मुलाची नावनोंदणी करावी लागते का?\n"
            "उत्तर: नाही. RBSK पथके शाळा आणि अंगणवाड्यांमध्ये स्वतः येतात. उपचारासाठी जवळच्या CHC किंवा जिल्हा रुग्णालयात जा."
        ),
        "text_ta": (
            "ராஷ்ட்ரிய பால் ஸ்வாஸ்த்ய கார்யக்ரம் (RBSK) பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: RBSK என்ன பரிசோதிக்கும்?\n"
            "ப: 4D: (1) பிறப்பு குறைபாடுகள் (பிளவு உதடு, கிளப் கால், இதய குறைபாடுகள்), (2) நோய்கள் (தோல், காது, கண், பல், இரத்தசோகை), (3) குறைபாடுகள் (ஊட்டச்சத்துக் குறைவு, வைட்டமின் D, இரும்பு), (4) வளர்ச்சி தாமதம் (கற்றல் குறைபாடு, பேச்சு தாமதம்).\n"
            "\n"
            "கே: RBSK சிகிச்சை இலவசமா?\n"
            "ப: ஆம். பரிசோதனை, பரிந்துரை, சிகிச்சை அனைத்தும் அரசு மருத்துவமனைகளில் இலவசம். பிறப்பு குறைபாடுகளுக்கு இலவச அறுவை சிகிச்சையும்.\n"
            "\n"
            "கே: பரிசோதனை எங்கு நடக்கும்?\n"
            "ப: அரசு பள்ளிகள் மற்றும் அங்கன்வாடி மையங்களில். RBSK கையடக்க சுகாதாரக் குழுக்கள் தொடர்ந்து வருகை தருகின்றன.\n"
            "\n"
            "கே: வயது வரம்பு என்ன?\n"
            "ப: பிறப்பு முதல் 18 வயது வரை.\n"
            "\n"
            "கே: குழந்தையை பதிவு செய்ய வேண்டுமா?\n"
            "ப: இல்லை. RBSK குழுக்கள் பள்ளிகள் மற்றும் அங்கன்வாடிகளுக்கு தாமாக வரும். சிகிச்சைக்கு அருகிலுள்ள CHC அல்லது மாவட்ட மருத்துவமனைக்குச் செல்லுங்கள்."
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

        "text_mr": (
            "सौभाग्य योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: वीज कनेक्शन मोफत आहे का?\n"
            "उत्तर: BPL कुटुंबांसाठी मोफत. APL ला 50 रुपयांच्या 10 हप्त्यांत 500 रुपये द्यावे लागतात.\n"
            "\n"
            "प्रश्न: मीटर मिळते का?\n"
            "उत्तर: होय. कनेक्शनमध्ये मीटर, सिंगल-पॉइंट वायरिंग आणि LED बल्ब समाविष्ट.\n"
            "\n"
            "प्रश्न: दुर्गम भागात कनेक्शन मिळते का?\n"
            "उत्तर: होय. ग्रिड पोहोचवणे शक्य नसलेल्या ठिकाणी सोलर ऑफ-ग्रिड उपाय (200Wp सोलर पॅनल, बॅटरी, LED, पंखा) दिले जातात.\n"
            "\n"
            "प्रश्न: अर्ज कसा करायचा?\n"
            "उत्तर: DISCOM (वीज कंपनी) किंवा ग्राम पंचायतीशी संपर्क करा. आधार आणि BPL कार्ड न्या.\n"
            "\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: 1912 (वीज हेल्पलाइन) वर कॉल करा किंवा स्थानिक DISCOM कार्यालयाशी संपर्क करा."
        ),
        "text_ta": (
            "சௌபாக்யா திட்டம் பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: மின் இணைப்பு இலவசமா?\n"
            "ப: BPL குடும்பங்களுக்கு இலவசம். APL க்கு 50 ரூபாய் வீதம் 10 தவணைகளில் 500 ரூபாய் செலுத்த வேண்டும்.\n"
            "\n"
            "கே: மீட்டர் கிடைக்குமா?\n"
            "ப: ஆம். இணைப்பில் மீட்டர், சிங்கிள்-பாயிண்ட் வயரிங், LED பல்ப் அடங்கும்.\n"
            "\n"
            "கே: தொலைவான பகுதிகளில் இணைப்பு கிடைக்குமா?\n"
            "ப: ஆம். கிரிட் செல்ல முடியாத இடங்களில் சோலார் ஆஃப்-கிரிட் தீர்வுகள் (200Wp சோலார் பேனல், பேட்டரி, LED, மின்விசிறி) வழங்கப்படும்.\n"
            "\n"
            "கே: எப்படி விண்ணப்பிப்பது?\n"
            "ப: DISCOM (மின் நிறுவனம்) அல்லது கிராம பஞ்சாயத்தை தொடர்பு கொள்ளுங்கள். ஆதார், BPL அட்டை எடுத்துச் செல்லுங்கள்.\n"
            "\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: 1912 (மின் ஹெல்ப்லைன்) அழைக்கவும் அல்லது உள்ளூர் DISCOM அலுவலகத்தை தொடர்பு கொள்ளவும்."
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

        "text_mr": (
            "स्वच्छ भारत मिशन (ग्रामीण) बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: शौचालय बांधण्यासाठी किती पैसे मिळतात?\n"
            "उत्तर: 12,000 रुपये सरकारी प्रोत्साहन (काही राज्यांत 15,000). बांधकाम, भिंती, छत आणि पाणी साठवण समाविष्ट.\n"
            "\n"
            "प्रश्न: पैसे कधी मिळतात?\n"
            "उत्तर: शौचालय बांधून सरकारी अधिकाऱ्याने तपासल्यानंतर. बँक खात्यात ट्रान्सफर.\n"
            "\n"
            "प्रश्न: कोणतेही शौचालय बांधता येते का?\n"
            "उत्तर: शौचालयात योग्य उपरचना (ट्विन पिट, सेप्टिक टँक), पाण्याची व्यवस्था आणि भिंती-छत-दरवाजा असायला हवे.\n"
            "\n"
            "प्रश्न: अर्ज कसा करायचा?\n"
            "उत्तर: ग्राम पंचायत किंवा खंड विकास कार्यालयात. आधार, BPL कार्ड न्या. काही राज्यांत sbm.gov.in वर ऑनलाइन.\n"
            "\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: 1969 (स्वच्छ भारत हेल्पलाइन), खंड विकास अधिकारी, किंवा swachhbharatmission.gov.in वर ऑनलाइन."
        ),
        "text_ta": (
            "சுவச்ச பாரத் மிஷன் (கிராமம்) பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: கழிப்பறை கட்ட எவ்வளவு பணம் கிடைக்கும்?\n"
            "ப: 12,000 ரூபாய் அரசு ஊக்கத்தொகை (சில மாநிலங்களில் 15,000). கட்டுமானம், சுவர்கள், கூரை, நீர் சேமிப்பு அடங்கும்.\n"
            "\n"
            "கே: பணம் எப்போது கிடைக்கும்?\n"
            "ப: கழிப்பறை கட்டி அரசு அதிகாரி சரிபார்த்த பிறகு. வங்கிக் கணக்கில் மாற்றம்.\n"
            "\n"
            "கே: எந்த வகை கழிப்பறையும் கட்டலாமா?\n"
            "ப: கழிப்பறையில் சரியான கட்டுமானம் (டுவின் பிட், செப்டிக் டேங்க்), நீர் வசதி, சுவர்கள்-கூரை-கதவு இருக்க வேண்டும்.\n"
            "\n"
            "கே: எப்படி விண்ணப்பிப்பது?\n"
            "ப: கிராம பஞ்சாயத் அல்லது வட்ட வளர்ச்சி அலுவலகத்தில். ஆதார், BPL அட்டை எடுத்துச் செல்லுங்கள். சில மாநிலங்களில் sbm.gov.in இல் ஆன்லைனில்.\n"
            "\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: 1969 (சுவச்ச பாரத் ஹெல்ப்லைன்), வட்ட வளர்ச்சி அதிகாரி, அல்லது swachhbharatmission.gov.in இல் ஆன்லைனில்."
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

        "text_mr": (
            "पीएम श्रम योगी मानधन योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: किती पेंशन मिळेल?\n"
            "उत्तर: 60 वर्षांनंतर दरमहा 3,000 रुपये हमी पेंशन.\n"
            "\n"
            "प्रश्न: किती योगदान द्यायचे?\n"
            "उत्तर: सामील होण्याच्या वयानुसार दरमहा 55 ते 200 रुपये. सरकारही तितकेच योगदान देते.\n"
            "\n"
            "प्रश्न: कोण पात्र आहे?\n"
            "उत्तर: 18-40 वर्षे वयाचे असंघटित कामगार, 15,000 रुपयांपर्यंत मासिक उत्पन्न. घरकामगार, फेरीवाले, बांधकाम कामगार, रिक्षाचालक, ऑटो ड्रायव्हर, धोबी, चांभार इ.\n"
            "\n"
            "प्रश्न: कोण पात्र नाही?\n"
            "उत्तर: EPFO/ESIC/NPS सदस्य, आयकरदाते, संघटित क्षेत्रातील कर्मचारी.\n"
            "\n"
            "प्रश्न: नोंदणी कशी करायची?\n"
            "उत्तर: जवळच्या CSC केंद्रात आधार आणि बचत खाते घेऊन जा. VLE ऑनलाइन नोंदणी करेल.\n"
            "\n"
            "प्रश्न: खाते कसे तपासायचे?\n"
            "उत्तर: maandhan.in वर किंवा 1800-267-6888 वर कॉल करा."
        ),
        "text_ta": (
            "பிஎம் ஸ்ரம் யோகி மான்தன் யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: எவ்வளவு ஓய்வூதியம் கிடைக்கும்?\n"
            "ப: 60 வயதுக்குப் பிறகு மாதம் 3,000 ரூபாய் உத்தரவாத ஓய்வூதியம்.\n"
            "\n"
            "கே: எவ்வளவு செலுத்த வேண்டும்?\n"
            "ப: சேரும் வயதைப் பொறுத்து மாதம் 55 முதல் 200 ரூபாய். அரசாங்கமும் அதே அளவு செலுத்தும்.\n"
            "\n"
            "கே: யார் தகுதியானவர்?\n"
            "ப: 18-40 வயது அமைப்புசாரா தொழிலாளர்கள், மாத வருமானம் 15,000 ரூபாய் வரை. வீட்டு வேலையாள், தெருவோர வியாபாரி, கட்டுமானத் தொழிலாளி, ரிக்ஷா இழுப்பவர், ஆட்டோ ஓட்டுநர், சலவை தொழிலாளி, செருப்புத் தைப்பவர் போன்றோர்.\n"
            "\n"
            "கே: யாருக்கு தகுதி இல்லை?\n"
            "ப: EPFO/ESIC/NPS உறுப்பினர்கள், வரி செலுத்துபவர்கள், அமைப்புசார் துறை ஊழியர்கள்.\n"
            "\n"
            "கே: எப்படி பதிவு செய்வது?\n"
            "ப: அருகிலுள்ள CSC மையத்தில் ஆதார் மற்றும் சேமிப்புக் கணக்குடன் செல்லுங்கள். VLE ஆன்லைனில் பதிவு செய்வார்.\n"
            "\n"
            "கே: கணக்கை எப்படி சரிபார்ப்பது?\n"
            "ப: maandhan.in இல் அல்லது 1800-267-6888 அழைக்கவும்."
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

        "text_mr": (
            "पीएम विश्वकर्मा योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: कोणते 18 व्यवसाय समाविष्ट आहेत?\n"
            "उत्तर: सुतार, नावबांधणी, कवचकार, लोहार, हातोडी/औजार बनवणारे, कुलूपकार, सोनार, कुंभार, शिल्पकार, चर्मकार, गवंडी, टोपली/चटई बनवणारे, बाहुली/खेळणी बनवणारे, न्हावी, माळकरी, धोबी, शिंपी, मासेमारी जाळी बनवणारे.\n"
            "\n"
            "प्रश्न: काय मिळते?\n"
            "उत्तर: (1) विश्वकर्मा प्रमाणपत्र आणि ID कार्ड, (2) 5-7 दिवस प्रशिक्षण + 500/दिवस भत्ता, (3) 15,000 पर्यंत औजार अनुदान, (4) पहिले कर्ज 1 लाख 5% व्याजाने नंतर 2 लाख, (5) डिजिटल पेमेंट प्रोत्साहन 1 रुपया/व्यवहार (कमाल 100/महिना), (6) मार्केटिंग सहाय्य.\n"
            "\n"
            "प्रश्न: कर्ज व्याजदर काय?\n"
            "उत्तर: 5% वार्षिक. उर्वरित व्याज सरकार देते. बँक दरांपेक्षा खूपच कमी.\n"
            "\n"
            "प्रश्न: नोंदणी कशी करायची?\n"
            "उत्तर: चरण 1: pmvishwakarma.gov.in वर आधार आणि मोबाइलने नोंदणी. चरण 2: ग्राम पंचायत/ULB सत्यापन. चरण 3: प्रशिक्षण, औजार आणि कर्ज अर्ज.\n"
            "\n"
            "प्रश्न: कुटुंबातल्या किती लोकांना लाभ मिळेल?\n"
            "उत्तर: एका कुटुंबातून (पती-पत्नी-अल्पवयीन मुले) फक्त एकच व्यक्ती."
        ),
        "text_ta": (
            "பிஎம் விஸ்வகர்மா யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: எந்த 18 தொழில்கள் உள்ளடங்கும்?\n"
            "ப: தச்சர், படகு செய்பவர், கவசமேகர், கொல்லர், சுத்தி/கருவி செய்பவர், பூட்டு செய்பவர், பொற்கொல்லர், குயவர், சிற்பி, செருப்புத் தைப்பவர், கொத்தனார், கூடை/பாய் பின்னுபவர், பொம்மை செய்பவர், நாவிதர், மாலை கட்டுபவர், சலவை தொழிலாளி, தையல்காரர், மீன் வலை செய்பவர்.\n"
            "\n"
            "கே: என்ன கிடைக்கும்?\n"
            "ப: (1) விஸ்வகர்மா சான்றிதழ் & ID அட்டை, (2) 5-7 நாள் பயிற்சி + 500/நாள் கொடுப்பனவு, (3) 15,000 வரை கருவி மானியம், (4) முதல் கடன் 1 லட்சம் 5% வட்டியில் பின்னர் 2 லட்சம், (5) டிஜிட்டல் பேமெண்ட் ஊக்கத்தொகை 1 ரூ/பரிவர்த்தனை (அதிகபட்சம் 100/மாதம்), (6) மார்க்கெட்டிங் உதவி.\n"
            "\n"
            "கே: கடன் வட்டி விகிதம் என்ன?\n"
            "ப: ஆண்டுக்கு 5%. மீதி வட்டியை அரசு செலுத்தும். வங்கி விகிதங்களை விட மிகக் குறைவு.\n"
            "\n"
            "கே: எப்படி பதிவு செய்வது?\n"
            "ப: படி 1: pmvishwakarma.gov.in இல் ஆதார் மற்றும் மொபைலுடன் பதிவு. படி 2: கிராம பஞ்சாயத்/ULB சரிபார்ப்பு. படி 3: பயிற்சி, கருவி, கடன் விண்ணப்பம்.\n"
            "\n"
            "கே: குடும்பத்தில் எத்தனை பேருக்கு பயன் கிடைக்கும்?\n"
            "ப: ஒரு குடும்பத்திலிருந்து (கணவன்-மனைவி-சிறுவர்) ஒருவர் மட்டுமே."
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

        "text_mr": (
            "जननी शिशु सुरक्षा कार्यक्रम (JSSK) बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: JSSK मध्ये काय-काय मोफत आहे?\n"
            "उत्तर: गर्भवती महिलांसाठी: मोफत प्रसुती (नॉर्मल आणि सी-सेक्शन), औषधे, तपासण्या, रक्त, जेवण, वाहतूक (घर ते रुग्णालय आणि परत). 30 दिवसांपर्यंतच्या आजारी नवजात: मोफत उपचार, औषधे, तपासण्या, रक्त, वाहतूक.\n"
            "\n"
            "प्रश्न: JSSK खाजगी रुग्णालयांत लागू आहे का?\n"
            "उत्तर: नाही. फक्त सरकारी आरोग्य केंद्रे - PHC, CHC, जिल्हा रुग्णालय, मेडिकल कॉलेज.\n"
            "\n"
            "प्रश्न: उत्पन्न किंवा BPL अट आहे का?\n"
            "उत्तर: नाही. सरकारी रुग्णालयात प्रसुती करणाऱ्या सर्व गर्भवती महिलांसाठी.\n"
            "\n"
            "प्रश्न: रुग्णालयाने पैसे मागितले तर?\n"
            "उत्तर: हे JSSK चे उल्लंघन. रुग्णालय अधीक्षक, मुख्य वैद्यकीय अधिकाऱ्याकडे तक्रार करा किंवा 1800-180-1104 वर कॉल करा.\n"
            "\n"
            "प्रश्न: सी-सेक्शन कव्हर आहे का?\n"
            "उत्तर: होय. सी-सेक्शन JSSK मध्ये पूर्णपणे मोफत.\n"
            "\n"
            "प्रश्न: मोफत वाहतूक कशी मिळेल?\n"
            "उत्तर: आशा कार्यकर्तीशी संपर्क करा किंवा 102 (अॅम्ब्युलन्स) वर कॉल करा. घर ते रुग्णालय, रेफरल आणि परत - सर्व मोफत.\n"
            "\n"
            "प्रश्न: नवजात किती दिवसांपर्यंत कव्हर आहे?\n"
            "उत्तर: आजारी नवजात जन्मानंतर 30 दिवसांपर्यंत मोफत उपचारास पात्र."
        ),
        "text_ta": (
            "ஜனனி சிசு சுரக்ஷா கார்யக்ரம் (JSSK) பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: JSSK இல் என்னென்ன இலவசம்?\n"
            "ப: கர்ப்பிணிப் பெண்களுக்கு: இலவச பிரசவம் (நார்மல் மற்றும் சி-செக்ஷன்), மருந்துகள், பரிசோதனைகள், இரத்தம், உணவு, போக்குவரத்து (வீட்டிலிருந்து மருத்துவமனை மற்றும் திரும்ப). 30 நாள் வரை நோய்வாய்ப்பட்ட புதிதாகப் பிறந்தவர்: இலவச சிகிச்சை, மருந்துகள், பரிசோதனைகள், இரத்தம், போக்குவரத்து.\n"
            "\n"
            "கே: JSSK தனியார் மருத்துவமனைகளில் பொருந்துமா?\n"
            "ப: இல்லை. அரசு சுகாதார நிலையங்கள் மட்டுமே - PHC, CHC, மாவட்ட மருத்துவமனை, மருத்துவக் கல்லூரி.\n"
            "\n"
            "கே: வருமானம் அல்லது BPL நிபந்தனை உள்ளதா?\n"
            "ப: இல்லை. அரசு மருத்துவமனையில் பிரசவிக்கும் அனைத்து கர்ப்பிணிப் பெண்களுக்கும்.\n"
            "\n"
            "கே: மருத்துவமனை பணம் கேட்டால்?\n"
            "ப: இது JSSK விதிமீறல். மருத்துவமனை கண்காணிப்பாளர், தலைமை மருத்துவ அதிகாரியிடம் புகார் செய்யுங்கள் அல்லது 1800-180-1104 அழைக்கவும்.\n"
            "\n"
            "கே: சி-செக்ஷன் கவர் ஆகுமா?\n"
            "ப: ஆம். சி-செக்ஷன் JSSK இல் முற்றிலும் இலவசம்.\n"
            "\n"
            "கே: இலவச போக்குவரத்து எப்படி பெறுவது?\n"
            "ப: ஆஷா ஊழியரை தொடர்பு கொள்ளுங்கள் அல்லது 102 (ஆம்புலன்ஸ்) அழைக்கவும். வீட்டிலிருந்து மருத்துவமனை, பரிந்துரை, திரும்புதல் - அனைத்தும் இலவசம்.\n"
            "\n"
            "கே: புதிதாகப் பிறந்த குழந்தை எத்தனை நாட்கள் கவர்?\n"
            "ப: நோய்வாய்ப்பட்ட புதிதாகப் பிறந்தவர் பிறந்த 30 நாட்கள் வரை இலவச சிகிச்சைக்கு தகுதியானவர்."
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

        "text_mr": (
            "पीएम कृषी सिंचन योजना बद्दल वारंवार विचारले जाणारे प्रश्न:\n"
            "\n"
            "प्रश्न: सूक्ष्म सिंचनावर किती सबसिडी मिळते?\n"
            "उत्तर: लहान आणि सीमांत शेतकरी: 55% सबसिडी. इतर शेतकरी: 45% सबसिडी - ड्रिप आणि स्प्रिंकलर सिंचन उपकरणांवर.\n"
            "\n"
            "प्रश्न: कोणत्या सिंचन प्रणाली कव्हर आहेत?\n"
            "उत्तर: ड्रिप सिंचन, स्प्रिंकलर, रेन गन, मायक्रो-स्प्रिंकलर आणि इतर सूक्ष्म सिंचन उपकरणे.\n"
            "\n"
            "प्रश्न: बोअरवेल/ट्यूबवेलवर सबसिडी मिळते का?\n"
            "उत्तर: काही राज्ये PMKSY हर खेत को पानी घटकांतर्गत बोअरवेल/ट्यूबवेलवर सबसिडी देतात. राज्य कृषी विभागाशी तपासा.\n"
            "\n"
            "प्रश्न: अर्ज कसा करायचा?\n"
            "उत्तर: जिल्हा कृषी/फलोत्पादन विभागाशी संपर्क करा. काही राज्यांत ऑनलाइन पोर्टल. जमिनीची कागदपत्रे, आधार आणि बँक माहिती न्या.\n"
            "\n"
            "प्रश्न: भाडेकरू शेतकरी अर्ज करू शकतात का?\n"
            "उत्तर: होय. भाडे/पट्ट्यावरील जमिनीचे शेतकरी योग्य भाडेपत्र कागदपत्रांसह अर्ज करू शकतात.\n"
            "\n"
            "प्रश्न: सबसिडी कधी येते?\n"
            "उत्तर: स्थापना आणि तपासणीनंतर 1-3 महिन्यांत बँक खात्यात.\n"
            "\n"
            "प्रश्न: तक्रार कुठे करायची?\n"
            "उत्तर: जिल्हा कृषी अधिकाऱ्याशी संपर्क करा किंवा 1800-180-1551 वर कॉल करा."
        ),
        "text_ta": (
            "பிஎம் கிருஷி சிஞ்சாய் யோஜனா பற்றிய அடிக்கடி கேட்கப்படும் கேள்விகள்:\n"
            "\n"
            "கே: நுண்ணிய நீர்ப்பாசனத்திற்கு எவ்வளவு மானியம் கிடைக்கும்?\n"
            "ப: சிறு மற்றும் விளிம்பு நிலை விவசாயிகள்: 55% மானியம். பிற விவசாயிகள்: 45% மானியம் - சொட்டு நீர் மற்றும் தெளிப்பான் நீர்ப்பாசன உபகரணங்களுக்கு.\n"
            "\n"
            "கே: எந்த நீர்ப்பாசன அமைப்புகள் கவர் ஆகும்?\n"
            "ப: சொட்டு நீர்ப்பாசனம், தெளிப்பான் அமைப்பு, ரெயின் கன், மைக்ரோ-ஸ்பிரிங்க்ளர், பிற நுண்ணிய நீர்ப்பாசன உபகரணங்கள்.\n"
            "\n"
            "கே: போர்வெல்/டியூப்வெல்லுக்கு மானியம் கிடைக்குமா?\n"
            "ப: சில மாநிலங்கள் PMKSY ஹர் கேத் கோ பானி கூறுவிற்குக் கீழ் போர்வெல்/டியூப்வெல்லுக்கு மானியம் அளிக்கின்றன. மாநில வேளாண் துறையிடம் சரிபார்க்கவும்.\n"
            "\n"
            "கே: எப்படி விண்ணப்பிப்பது?\n"
            "ப: மாவட்ட வேளாண்/தோட்டக்கலைத் துறையை தொடர்பு கொள்ளுங்கள். சில மாநிலங்களில் ஆன்லைன் போர்ட்டல். நில ஆவணங்கள், ஆதார், வங்கி விவரங்கள் எடுத்துச் செல்லுங்கள்.\n"
            "\n"
            "கே: குத்தகை விவசாயிகள் விண்ணப்பிக்கலாமா?\n"
            "ப: ஆம். குத்தகை/வாடகை நிலம் உள்ள விவசாயிகளும் சரியான குத்தகை ஆவணங்களுடன் விண்ணப்பிக்கலாம்.\n"
            "\n"
            "கே: மானியம் எப்போது வரும்?\n"
            "ப: நிறுவல் மற்றும் சரிபார்ப்புக்குப் பிறகு 1-3 மாதங்களில் வங்கிக் கணக்கில்.\n"
            "\n"
            "கே: புகார் எங்கு செய்வது?\n"
            "ப: மாவட்ட வேளாண் அதிகாரியை தொடர்பு கொள்ளுங்கள் அல்லது 1800-180-1551 அழைக்கவும்."
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
        for lang in ["en", "hi", "mr", "ta"]:
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
