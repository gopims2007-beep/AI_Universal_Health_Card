-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.users (
  id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
  email character varying NOT NULL,
  password_hash character varying NOT NULL,
  role character varying NOT NULL,
  full_name character varying NOT NULL,
  phone character varying,
  is_active boolean NOT NULL,
  is_email_verified boolean NOT NULL,
  created_at timestamp without time zone NOT NULL,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);
CREATE TABLE public.patient_profiles (
  id integer NOT NULL DEFAULT nextval('patient_profiles_id_seq'::regclass),
  user_id integer NOT NULL UNIQUE,
  card_id character varying NOT NULL,
  date_of_birth date,
  gender character varying,
  blood_group character varying,
  height_cm double precision,
  weight_kg double precision,
  bmi double precision,
  address text,
  emergency_contact_name character varying,
  emergency_contact_phone character varying,
  emergency_contact_relation character varying,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT patient_profiles_pkey PRIMARY KEY (id),
  CONSTRAINT patient_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.audit_logs (
  id integer NOT NULL DEFAULT nextval('audit_logs_id_seq'::regclass),
  user_id integer,
  action character varying NOT NULL,
  resource_type character varying NOT NULL,
  resource_id character varying,
  ip_address character varying,
  created_at timestamp without time zone NOT NULL,
  CONSTRAINT audit_logs_pkey PRIMARY KEY (id),
  CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.one_time_tokens (
  id integer NOT NULL DEFAULT nextval('one_time_tokens_id_seq'::regclass),
  user_id integer NOT NULL,
  token_hash character varying NOT NULL,
  purpose character varying NOT NULL,
  expires_at timestamp without time zone NOT NULL,
  used boolean NOT NULL,
  CONSTRAINT one_time_tokens_pkey PRIMARY KEY (id),
  CONSTRAINT one_time_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.medical_history (
  id integer NOT NULL DEFAULT nextval('medical_history_id_seq'::regclass),
  patient_id integer NOT NULL,
  diseases json,
  allergies json,
  current_medications json,
  surgery_history json,
  vaccination_records json,
  insurance_details json,
  notes text,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT medical_history_pkey PRIMARY KEY (id),
  CONSTRAINT medical_history_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patient_profiles(id)
);
CREATE TABLE public.medical_reports (
  id integer NOT NULL DEFAULT nextval('medical_reports_id_seq'::regclass),
  patient_id integer NOT NULL,
  uploaded_by_id integer NOT NULL,
  report_type character varying NOT NULL,
  original_filename character varying NOT NULL,
  stored_filename character varying NOT NULL UNIQUE,
  mime_type character varying NOT NULL,
  size_bytes integer NOT NULL,
  extracted_text text,
  uploaded_at timestamp without time zone NOT NULL,
  CONSTRAINT medical_reports_pkey PRIMARY KEY (id),
  CONSTRAINT medical_reports_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patient_profiles(id),
  CONSTRAINT medical_reports_uploaded_by_id_fkey FOREIGN KEY (uploaded_by_id) REFERENCES public.users(id)
);
CREATE TABLE public.qr_codes (
  id integer NOT NULL DEFAULT nextval('qr_codes_id_seq'::regclass),
  patient_id integer NOT NULL,
  qr_token character varying NOT NULL,
  emergency_url character varying NOT NULL,
  created_at timestamp without time zone NOT NULL,
  revoked boolean NOT NULL,
  CONSTRAINT qr_codes_pkey PRIMARY KEY (id),
  CONSTRAINT qr_codes_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patient_profiles(id)
);
CREATE TABLE public.emergency_documents (
  id integer NOT NULL DEFAULT nextval('emergency_documents_id_seq'::regclass),
  patient_id integer NOT NULL,
  emergency_id character varying NOT NULL,
  file_name character varying NOT NULL,
  google_drive_url character varying NOT NULL,
  description text,
  document_category character varying,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT emergency_documents_pkey PRIMARY KEY (id),
  CONSTRAINT emergency_documents_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patient_profiles(id)
);
CREATE TABLE public.consent_tokens (
  id integer NOT NULL DEFAULT nextval('consent_tokens_id_seq'::regclass),
  patient_id integer NOT NULL,
  doctor_user_id integer NOT NULL,
  token_hash character varying NOT NULL UNIQUE,
  expires_at timestamp without time zone NOT NULL,
  revoked boolean NOT NULL,
  CONSTRAINT consent_tokens_pkey PRIMARY KEY (id),
  CONSTRAINT consent_tokens_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patient_profiles(id),
  CONSTRAINT consent_tokens_doctor_user_id_fkey FOREIGN KEY (doctor_user_id) REFERENCES public.users(id)
);
CREATE TABLE public.ai_analyses (
  id integer NOT NULL DEFAULT nextval('ai_analyses_id_seq'::regclass),
  report_id integer NOT NULL,
  model_name character varying NOT NULL,
  status character varying NOT NULL,
  summary text NOT NULL,
  key_insights json,
  risk_label character varying,
  risk_score double precision,
  recommendations json,
  disclaimer text NOT NULL,
  created_at timestamp without time zone NOT NULL,
  CONSTRAINT ai_analyses_pkey PRIMARY KEY (id),
  CONSTRAINT ai_analyses_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.medical_reports(id)
);