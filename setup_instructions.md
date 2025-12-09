# Setup Instructions

1. Fill .env
2. Install dependencies
3. Run backend + frontend
venv\Scripts\activate
uvicorn backend.main:app --reload

to test from the root run this ->
python -m backend.scripts.test_document_processing(process)
python -m backend.scripts.build_vector_store(process)
python -m backend.scripts.test_llm(process)

Always run build_vector_store.py after updating/creating the legal docs(india.json,canada.json etc)


cd lexivoice/frontend
streamlit run app.py
db - jayrv

CANADA
🇨🇦 15 Questions to Test Your RAG Pipeline

How many hours can international students work on a study permit in Canada?

Do students need a separate work permit to work off-campus in Canada?

How long can a graduate get a work permit after finishing a 2-year program in Canada?

Can a PGWP be renewed or extended in Canada?

What is the federal minimum wage in Canada in 2024?

How many paid vacation weeks do federally regulated employees get after one year?

Am I protected from dismissal if I take medical leave in Canada?

Can an employee request flexible working hours from their employer in Canada?

Is false or misleading advertising illegal in Canada?

Do consumers have warranty rights even if they don’t buy an extended warranty?

Can companies use personal information without consent under PIPEDA?

What is the penalty for fraud under the Canadian Criminal Code?

Who can request government records under the Access to Information Act?

Can a student do a co-op or internship without a work permit in Canada?

Who is responsible for ensuring workplace safety under the Canada Labour Code?



INDIA

🇮🇳 15 Queries Based on Indian Laws (For RAG Testing)

Can an international student work in India on a student visa?

Can a foreign employee change their employer on an Indian employment visa?

What is the minimum wage law in India?

Can I get a refund if a product is defective under Indian consumer law?

How many hours can a factory worker legally work per day in India?

What is displacement allowance for migrant workers in India?

Is bonded labour legal in India?

What are the eligibility rules for Indian citizenship under the Citizenship Amendment Act 2019?

What happens if an employer does not pay statutory bonuses in India?

Does Indian law require equal pay for men and women?

Can a company be punished for failing to protect personal data in India?

What is the punishment for murder under Indian law?

How do I file an FIR for a cognizable offence in India?

Which companies are required to spend on Corporate Social Responsibility in India?

What deductions are allowed under Section 80C of the Income Tax Act?



USA

🇺🇸 15 Questions for U.S. Law RAG Testing

Can F-1 international students work in the United States?

How long can an H-1B visa worker stay in the U.S.?

What is the federal minimum wage in the United States?

Are advertisements required to be truthful under U.S. law?

When is overtime pay required in the U.S.?

How much unpaid leave can employees take under FMLA?

What protections does the ADA give to employees with disabilities?

Does U.S. law protect workers from discrimination based on gender or race?

Can men and women be paid differently for the same job in the U.S.?

Does the ADEA protect employees over age 40?

What safety obligations do employers have under OSHA?

What benefits do injured federal workers receive under workers' compensation?

What is HIPAA and what does it protect?

What rights do consumers have under the Fair Debt Collection Practices Act?

How can someone adjust status to a U.S. green card through employment?


