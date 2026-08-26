from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from livekit.agents import ToolError

from clinic import Appointment, Clinic, Patient, Provider, ProviderPanel, Slot
from reception import PatientIntakeAgent

NOW = datetime(2026, 8, 17, 9, 0)


def clinic() -> Clinic:
    provider = Provider(
        id="alvarez",
        name="Doctor Elena Alvarez",
        specialty="Family Medicine",
    )
    patient = Patient(
        chart_id="MRN10001",
        first_name="Dolores",
        last_name="Whitaker",
        date_of_birth=datetime(1958, 3, 14).date(),
    )
    return Clinic(
        now=NOW,
        providers=[provider],
        patients=[patient],
        slots=[
            Slot(provider_id="alvarez", start=datetime(2026, 8, 18, 13, 30)),
            Slot(provider_id="alvarez", start=datetime(2026, 8, 20, 10, 30)),
        ],
        appointments=[
            Appointment(
                id="APT2001",
                chart_id=patient.chart_id,
                provider_id="alvarez",
                start=datetime(2026, 8, 19, 10, 30),
                visit_type="follow_up",
            )
        ],
    )


def test_reference_agent_has_one_small_static_tool_surface() -> None:
    agent = PatientIntakeAgent(clinic=clinic(), greet=False)

    assert {tool.info.name for tool in agent.tools} == {
        "book_appointment",
        "find_open_times",
        "manage_appointment",
        "read_practice_information",
        "record_emergency_escalation",
        "record_previsit_intake",
        "take_message",
        "update_insurance",
    }


def test_reference_agent_contains_no_workflow_framework() -> None:
    source = Path("src")
    ignored = {"__pycache__", ".venv"}
    shipped = "\n".join(
        path.read_text(encoding="utf-8")
        for path in source.rglob("*.py")
        if not ignored & set(path.parts)
    )

    for forbidden in (
        "AgentTask",
        "EmergencyRedFlag",
        "PracticeTopic",
        "Toolset",
        "update_agent",
        "update_tools",
    ):
        assert forbidden not in shipped


async def test_new_patient_booking_registers_and_books_in_one_tool_call() -> None:
    records = clinic()
    agent = PatientIntakeAgent(clinic=records, greet=False)
    slot = records.open_slots()[0]

    await agent.find_open_times(
        patient_status="new", last_name="Parlo", date_of_birth="1989-08-01"
    )
    result = await agent.book_appointment(
        patient_status="new",
        last_name="Parlo",
        date_of_birth="1989-08-01",
        slot_id=slot.id,
        visit_type="sick_visit",
        reason="foot pain",
        first_name="Shayne",
    )

    patient = records.find_patient("Parlo", datetime(1989, 8, 1).date())
    assert patient.registered_on_this_call
    assert records.scheduled_for(patient.chart_id)[0].slot == slot
    assert "Doctor Elena Alvarez" in result
    assert "Tuesday, August 18 at 1:30 PM" in result


async def test_established_patient_can_list_and_move_an_appointment() -> None:
    records = clinic()
    agent = PatientIntakeAgent(clinic=records, greet=False)

    listed = await agent.manage_appointment(
        action="list",
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        caller_relationship="the patient",
    )
    assert "APT2001" in listed
    assert "Wednesday, August 19 at 10:30 AM" in listed

    destination = records.open_slots()[0]
    moved = await agent.manage_appointment(
        action="reschedule",
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        caller_relationship="the patient",
        appointment_id="APT2001",
        new_slot_id=destination.id,
    )
    assert records.appointment("APT2001").slot == destination
    assert "Tuesday, August 18 at 1:30 PM" in moved


async def test_established_status_uses_the_existing_chart_without_registration() -> (
    None
):
    records = clinic()
    agent = PatientIntakeAgent(clinic=records, greet=False)
    slot = records.open_slots()[0]

    await agent.book_appointment(
        patient_status="established",
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        slot_id=slot.id,
        visit_type="sick_visit",
        reason="rash",
    )

    assert len(records.patients) == 1
    assert records.scheduled_for("MRN10001")[-1].slot == slot


async def test_exact_time_search_names_the_unavailable_time() -> None:
    agent = PatientIntakeAgent(clinic=clinic(), greet=False)

    result = await agent.find_open_times(
        patient_status="new",
        date_of_birth="1990-11-11",
        last_name="Adeyemi",
        preferred_date="2026-08-20",
        time_of_day="morning",
        preferred_time="07:00",
    )

    assert "No suitable appointment is open at 7:00 AM on Thursday, August 20" in result
    assert "10:30 AM" in result


async def test_child_search_redirects_an_adult_provider_to_pediatrics() -> None:
    adult = Provider(
        id="alvarez",
        name="Doctor Elena Alvarez",
        specialty="Family Medicine",
        panel=ProviderPanel.ADULT,
    )
    pediatrician = Provider(
        id="raman",
        name="Doctor Priya Raman",
        specialty="Pediatrics",
        panel=ProviderPanel.PEDIATRIC,
    )
    records = Clinic(
        now=NOW,
        providers=[adult, pediatrician],
        slots=[Slot(provider_id="raman", start=datetime(2026, 8, 19, 10, 30))],
    )
    agent = PatientIntakeAgent(clinic=records, greet=False)

    result = await agent.find_open_times(
        patient_status="new",
        date_of_birth="2019-11-05",
        last_name="Whitaker",
        provider_id="alvarez",
    )

    assert "Patients under 18 are seen by Doctor Priya Raman" in result
    assert "Wednesday, August 19 at 10:30 AM" in result


async def test_established_availability_matches_identity_before_returning_slots() -> (
    None
):
    agent = PatientIntakeAgent(clinic=clinic(), greet=False)

    with pytest.raises(ToolError, match="No patient matched"):
        await agent.find_open_times(
            patient_status="established",
            last_name="Whitaker",
            date_of_birth="1958-03-15",
        )

    result = await agent.find_open_times(
        patient_status="established",
        last_name="Whitaker",
        date_of_birth="1958-03-14",
    )
    assert "Open appointments" in result


async def test_record_tools_write_the_clinic_state_directly() -> None:
    records = clinic()
    agent = PatientIntakeAgent(clinic=records, greet=False)

    await agent.update_insurance(
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        carrier="Meridian Choice",
        member_id="MC123",
    )
    await agent.take_message(
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        kind="prescription_refill",
        summary="Lisinopril refill requested",
    )
    await agent.record_previsit_intake(
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        chief_complaint="swollen knee",
        symptom_duration="two weeks",
        medications=["lisinopril", "vitamin D"],
        allergies=["penicillin - hives"],
        conditions=["high blood pressure"],
        pharmacy="Bridge Street Pharmacy",
    )

    patient = records.find_patient("Whitaker", datetime(1958, 3, 14).date())
    intake = records.intake_for(patient.chart_id)
    assert patient.insurance and patient.insurance.carrier == "Meridian Choice"
    assert [message.kind for message in records.messages] == ["prescription_refill"]
    assert intake.medications == ["lisinopril", "vitamin D"]
    assert intake.allergies == ["penicillin - hives"]
    assert intake.disposition.value == "completed"

    duplicate = await agent.take_message(
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        kind="prescription_refill",
        summary="Send it immediately",
    )
    assert "No second message was sent" in duplicate
    assert "within two business days" in duplicate
    assert len(records.messages) == 1


async def test_practice_information_is_returned_without_topic_classification() -> None:
    agent = PatientIntakeAgent(clinic=clinic(), greet=False)

    guide = await agent.read_practice_information()

    assert "412 Maplewood Avenue" in guide
    assert "Interpreter services are free" in guide
    assert "closed Saturday and Sunday" in guide


async def test_emergency_direction_is_durable_and_unambiguous() -> None:
    records = clinic()
    agent = PatientIntakeAgent(clinic=records, greet=False)

    result = await agent.record_emergency_escalation(
        reported_symptoms="heavy chest pressure spreading down the left arm",
    )

    assert records.escalations
    assert (
        result == "Emergency escalation recorded. Give the appropriate direction now."
    )


async def test_new_status_with_a_matching_chart_uses_it_instead_of_registering() -> (
    None
):
    records = clinic()
    agent = PatientIntakeAgent(clinic=records, greet=False)

    result = await agent.find_open_times(
        patient_status="new", last_name="Whitaker", date_of_birth="1958-03-14"
    )
    assert "already has a chart" in result
    assert "Open appointments" in result

    await agent.book_appointment(
        patient_status="new",
        last_name="Whitaker",
        date_of_birth="1958-03-14",
        slot_id=records.open_slots()[0].id,
        visit_type="sick_visit",
        reason="rash",
        first_name="Dolores",
    )
    assert len(records.patients) == 1


async def test_registration_needs_a_search_under_the_same_name_and_birth_date() -> None:
    records = clinic()
    agent = PatientIntakeAgent(clinic=records, greet=False)
    slot = records.open_slots()[0]

    await agent.find_open_times(
        patient_status="new", last_name="Thompson", date_of_birth="1991-09-12"
    )
    with pytest.raises(ToolError, match="find_open_times"):
        await agent.book_appointment(
            patient_status="new",
            last_name="Venkat",
            date_of_birth="1991-09-12",
            slot_id=slot.id,
            visit_type="sick_visit",
            reason="sore throat",
            first_name="Priya",
        )
    assert len(records.patients) == 1

    await agent.find_open_times(
        patient_status="new", last_name="Venkat", date_of_birth="1991-09-12"
    )
    await agent.book_appointment(
        patient_status="new",
        last_name="Venkat",
        date_of_birth="1991-09-12",
        slot_id=slot.id,
        visit_type="sick_visit",
        reason="sore throat",
        first_name="Priya",
    )
    assert [p.last_name for p in records.patients if p.registered_on_this_call] == [
        "Venkat"
    ]


async def test_a_failed_lookup_tells_the_model_not_to_offer_times() -> None:
    agent = PatientIntakeAgent(clinic=clinic(), greet=False)

    with pytest.raises(ToolError, match="Do not offer any appointment times"):
        await agent.find_open_times(
            patient_status="established",
            last_name="Whitaker",
            date_of_birth="1958-03-15",
        )
