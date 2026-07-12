--
-- PostgreSQL database dump
--

\restrict RLhiqAI4iTrnDkM2GSu1bOB35ebo0n9TdogVysqCrxbeCX2ev5omQav7Sy1eK3B

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: chat_role; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.chat_role AS ENUM (
    'user',
    'assistant',
    'tool'
);


ALTER TYPE public.chat_role OWNER TO transitops;

--
-- Name: driver_status; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.driver_status AS ENUM (
    'available',
    'on_trip',
    'off_duty',
    'suspended'
);


ALTER TYPE public.driver_status OWNER TO transitops;

--
-- Name: expense_type; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.expense_type AS ENUM (
    'toll',
    'parking',
    'fine',
    'loading',
    'other'
);


ALTER TYPE public.expense_type OWNER TO transitops;

--
-- Name: maintenance_status; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.maintenance_status AS ENUM (
    'open',
    'closed'
);


ALTER TYPE public.maintenance_status OWNER TO transitops;

--
-- Name: trip_status; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.trip_status AS ENUM (
    'draft',
    'dispatched',
    'completed',
    'cancelled'
);


ALTER TYPE public.trip_status OWNER TO transitops;

--
-- Name: user_role; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.user_role AS ENUM (
    'fleet_manager',
    'driver',
    'safety_officer',
    'financial_analyst'
);


ALTER TYPE public.user_role OWNER TO transitops;

--
-- Name: vehicle_status; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.vehicle_status AS ENUM (
    'available',
    'on_trip',
    'in_shop',
    'retired'
);


ALTER TYPE public.vehicle_status OWNER TO transitops;

--
-- Name: vehicle_type; Type: TYPE; Schema: public; Owner: transitops
--

CREATE TYPE public.vehicle_type AS ENUM (
    'truck',
    'van',
    'mini_truck',
    'trailer'
);


ALTER TYPE public.vehicle_type OWNER TO transitops;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_settings; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.ai_settings (
    id smallint DEFAULT 1 NOT NULL,
    chatbot_enabled boolean DEFAULT true NOT NULL,
    model character varying(80) DEFAULT 'anthropic/claude-3.5-haiku'::character varying NOT NULL,
    temperature numeric(3,2) DEFAULT 0.30 NOT NULL,
    max_tokens integer DEFAULT 1024 NOT NULL,
    system_prompt text NOT NULL,
    role_tool_permissions jsonb NOT NULL,
    updated_by uuid,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_ai_settings_max_tokens CHECK (((max_tokens >= 128) AND (max_tokens <= 8192))),
    CONSTRAINT ck_ai_settings_singleton CHECK ((id = 1)),
    CONSTRAINT ck_ai_settings_temperature CHECK (((temperature >= (0)::numeric) AND (temperature <= (2)::numeric)))
);


ALTER TABLE public.ai_settings OWNER TO transitops;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO transitops;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.audit_logs (
    id bigint NOT NULL,
    user_id uuid,
    action character varying(60) NOT NULL,
    entity character varying(30) NOT NULL,
    entity_id uuid,
    payload jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO transitops;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: transitops
--

CREATE SEQUENCE public.audit_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO transitops;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: transitops
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.chat_messages (
    session_id uuid NOT NULL,
    role public.chat_role NOT NULL,
    content text NOT NULL,
    tool_calls jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


ALTER TABLE public.chat_messages OWNER TO transitops;

--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.chat_sessions (
    user_id uuid NOT NULL,
    title character varying(120) DEFAULT 'New chat'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


ALTER TABLE public.chat_sessions OWNER TO transitops;

--
-- Name: drivers; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.drivers (
    full_name character varying(120) NOT NULL,
    license_number character varying(30) NOT NULL,
    license_category character varying(10) NOT NULL,
    license_expiry date NOT NULL,
    contact_number character varying(15) NOT NULL,
    safety_score numeric(5,2) DEFAULT 100 NOT NULL,
    status public.driver_status DEFAULT 'available'::public.driver_status NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_drivers_contact CHECK (((contact_number)::text ~ '^[0-9+][0-9 -]{7,14}$'::text)),
    CONSTRAINT ck_drivers_safety_score CHECK (((safety_score >= (0)::numeric) AND (safety_score <= (100)::numeric)))
);


ALTER TABLE public.drivers OWNER TO transitops;

--
-- Name: expenses; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.expenses (
    vehicle_id uuid NOT NULL,
    trip_id uuid,
    type public.expense_type NOT NULL,
    amount numeric(12,2) NOT NULL,
    description character varying(255),
    incurred_at date DEFAULT CURRENT_DATE NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    CONSTRAINT ck_expenses_amount_pos CHECK ((amount > (0)::numeric))
);


ALTER TABLE public.expenses OWNER TO transitops;

--
-- Name: fuel_logs; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.fuel_logs (
    vehicle_id uuid NOT NULL,
    trip_id uuid,
    liters numeric(8,2) NOT NULL,
    cost numeric(12,2) NOT NULL,
    odometer_at_fill numeric(12,2),
    filled_at date DEFAULT CURRENT_DATE NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    CONSTRAINT ck_fuel_cost_nonneg CHECK ((cost >= (0)::numeric)),
    CONSTRAINT ck_fuel_liters_pos CHECK ((liters > (0)::numeric)),
    CONSTRAINT ck_fuel_odometer_nonneg CHECK (((odometer_at_fill IS NULL) OR (odometer_at_fill >= (0)::numeric)))
);


ALTER TABLE public.fuel_logs OWNER TO transitops;

--
-- Name: maintenance_logs; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.maintenance_logs (
    vehicle_id uuid NOT NULL,
    title character varying(120) NOT NULL,
    description text,
    cost numeric(12,2) DEFAULT 0 NOT NULL,
    status public.maintenance_status DEFAULT 'open'::public.maintenance_status NOT NULL,
    opened_at timestamp with time zone DEFAULT now() NOT NULL,
    closed_at timestamp with time zone,
    created_by uuid NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    CONSTRAINT ck_maint_closed CHECK (((status <> 'closed'::public.maintenance_status) OR (closed_at IS NOT NULL)))
);


ALTER TABLE public.maintenance_logs OWNER TO transitops;

--
-- Name: trip_code_seq; Type: SEQUENCE; Schema: public; Owner: transitops
--

CREATE SEQUENCE public.trip_code_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.trip_code_seq OWNER TO transitops;

--
-- Name: trips; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.trips (
    trip_code character varying(12) NOT NULL,
    source character varying(120) NOT NULL,
    destination character varying(120) NOT NULL,
    vehicle_id uuid NOT NULL,
    driver_id uuid NOT NULL,
    cargo_weight_kg numeric(10,2) NOT NULL,
    planned_distance_km numeric(10,2) NOT NULL,
    revenue numeric(14,2) DEFAULT 0 NOT NULL,
    status public.trip_status DEFAULT 'draft'::public.trip_status NOT NULL,
    start_odometer numeric(12,2),
    end_odometer numeric(12,2),
    notes text,
    created_by uuid NOT NULL,
    dispatched_at timestamp with time zone,
    completed_at timestamp with time zone,
    cancelled_at timestamp with time zone,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_trips_completed_fields CHECK (((status <> 'completed'::public.trip_status) OR ((start_odometer IS NOT NULL) AND (end_odometer IS NOT NULL)))),
    CONSTRAINT ck_trips_odometer CHECK (((end_odometer IS NULL) OR (start_odometer IS NULL) OR (end_odometer >= start_odometer)))
);


ALTER TABLE public.trips OWNER TO transitops;

--
-- Name: users; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.users (
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    full_name character varying(120) NOT NULL,
    role public.user_role NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_users_email CHECK (((email)::text ~* '^[A-Za-z0-9._%%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text))
);


ALTER TABLE public.users OWNER TO transitops;

--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: transitops
--

CREATE TABLE public.vehicles (
    registration_number character varying(20) NOT NULL,
    name character varying(80) NOT NULL,
    type public.vehicle_type NOT NULL,
    max_load_capacity_kg numeric(10,2) NOT NULL,
    odometer_km numeric(12,2) DEFAULT 0 NOT NULL,
    acquisition_cost numeric(14,2) NOT NULL,
    region character varying(40) NOT NULL,
    status public.vehicle_status DEFAULT 'available'::public.vehicle_status NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_vehicles_acqcost_pos CHECK ((acquisition_cost > (0)::numeric)),
    CONSTRAINT ck_vehicles_capacity_pos CHECK ((max_load_capacity_kg > (0)::numeric)),
    CONSTRAINT ck_vehicles_odometer_nonneg CHECK ((odometer_km >= (0)::numeric))
);


ALTER TABLE public.vehicles OWNER TO transitops;

--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: ai_settings ai_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.ai_settings
    ADD CONSTRAINT ai_settings_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: drivers drivers_license_number_key; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_license_number_key UNIQUE (license_number);


--
-- Name: drivers drivers_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: fuel_logs fuel_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.fuel_logs
    ADD CONSTRAINT fuel_logs_pkey PRIMARY KEY (id);


--
-- Name: maintenance_logs maintenance_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.maintenance_logs
    ADD CONSTRAINT maintenance_logs_pkey PRIMARY KEY (id);


--
-- Name: trips trips_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_pkey PRIMARY KEY (id);


--
-- Name: trips trips_trip_code_key; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_trip_code_key UNIQUE (trip_code);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_registration_number_key; Type: CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_registration_number_key UNIQUE (registration_number);


--
-- Name: ix_chat_messages_session; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_chat_messages_session ON public.chat_messages USING btree (session_id, created_at);


--
-- Name: ix_drivers_license_expiry; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_drivers_license_expiry ON public.drivers USING btree (license_expiry);


--
-- Name: ix_drivers_status; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_drivers_status ON public.drivers USING btree (status);


--
-- Name: ix_expenses_vehicle_date; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_expenses_vehicle_date ON public.expenses USING btree (vehicle_id, incurred_at);


--
-- Name: ix_fuel_vehicle_date; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_fuel_vehicle_date ON public.fuel_logs USING btree (vehicle_id, filled_at);


--
-- Name: ix_maint_vehicle; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_maint_vehicle ON public.maintenance_logs USING btree (vehicle_id);


--
-- Name: ix_trips_driver; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_trips_driver ON public.trips USING btree (driver_id);


--
-- Name: ix_trips_status; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_trips_status ON public.trips USING btree (status);


--
-- Name: ix_trips_vehicle; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_trips_vehicle ON public.trips USING btree (vehicle_id);


--
-- Name: ix_vehicles_status; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_vehicles_status ON public.vehicles USING btree (status);


--
-- Name: ix_vehicles_type_region; Type: INDEX; Schema: public; Owner: transitops
--

CREATE INDEX ix_vehicles_type_region ON public.vehicles USING btree (type, region);


--
-- Name: uq_maint_open_per_vehicle; Type: INDEX; Schema: public; Owner: transitops
--

CREATE UNIQUE INDEX uq_maint_open_per_vehicle ON public.maintenance_logs USING btree (vehicle_id) WHERE (status = 'open'::public.maintenance_status);


--
-- Name: uq_trips_active_driver; Type: INDEX; Schema: public; Owner: transitops
--

CREATE UNIQUE INDEX uq_trips_active_driver ON public.trips USING btree (driver_id) WHERE (status = 'dispatched'::public.trip_status);


--
-- Name: uq_trips_active_vehicle; Type: INDEX; Schema: public; Owner: transitops
--

CREATE UNIQUE INDEX uq_trips_active_vehicle ON public.trips USING btree (vehicle_id) WHERE (status = 'dispatched'::public.trip_status);


--
-- Name: ai_settings ai_settings_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.ai_settings
    ADD CONSTRAINT ai_settings_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: expenses expenses_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: expenses expenses_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.trips(id) ON DELETE SET NULL;


--
-- Name: expenses expenses_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE RESTRICT;


--
-- Name: fuel_logs fuel_logs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.fuel_logs
    ADD CONSTRAINT fuel_logs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: fuel_logs fuel_logs_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.fuel_logs
    ADD CONSTRAINT fuel_logs_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.trips(id) ON DELETE SET NULL;


--
-- Name: fuel_logs fuel_logs_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.fuel_logs
    ADD CONSTRAINT fuel_logs_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE RESTRICT;


--
-- Name: maintenance_logs maintenance_logs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.maintenance_logs
    ADD CONSTRAINT maintenance_logs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: maintenance_logs maintenance_logs_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.maintenance_logs
    ADD CONSTRAINT maintenance_logs_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE RESTRICT;


--
-- Name: trips trips_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: trips trips_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(id) ON DELETE RESTRICT;


--
-- Name: trips trips_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: transitops
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict RLhiqAI4iTrnDkM2GSu1bOB35ebo0n9TdogVysqCrxbeCX2ev5omQav7Sy1eK3B

