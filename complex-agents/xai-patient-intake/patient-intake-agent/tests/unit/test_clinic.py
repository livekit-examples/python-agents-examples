from datetime import date, datetime

import pytest

from clinic import (
    Appointment,
    Clinic,
    Insurance,
    Patient,
    Provider,
    ProviderEligibilityError,
    ProviderPanel,
    Slot,
    open_clinic,
)

NOW = datetime(2026, 8, 17, 9, 0)


def patient() -> Patient:
    return Patient(
        chart_id="MRN1",
        first_name="Dolores",
        last_name="Whitaker",
        date_of_birth=date(1958, 3, 14),
    )


def clinic() -> Clinic:
    provider = Provider(
        id="alvarez",
        name="Doctor Alvarez",
        specialty="Family Medicine",
    )
    return Clinic(
        now=NOW,
        providers=[provider],
        patients=[patient()],
        slots=[
            Slot(provider_id="alvarez", start=datetime(2026, 8, 18, 9, 30)),
            Slot(provider_id="alvarez", start=datetime(2026, 8, 19, 13, 30)),
        ],
    )


def test_slots_are_stable_and_searchable_by_date() -> None:
    records = clinic()
    slot = records.open_slots(on_date=date(2026, 8, 19))[0]

    assert slot.id == Slot(provider_id="alvarez", start=slot.start).id
    assert slot.start == datetime(2026, 8, 19, 13, 30)


def test_booking_cancel_and_reschedule_move_real_slots() -> None:
    records = clinic()
    first, second = records.open_slots()
    booked = records.book(
        patient=records.patients[0],
        slot_id=first.id,
        visit_type="sick_visit",
    )

    assert first not in records.open_slots()

    records.reschedule(booked.id, second.id)
    assert booked.slot == second
    assert first in records.open_slots()

    records.cancel(booked.id)
    assert booked.status == "cancelled"
    assert second in records.open_slots()


def test_new_patients_cannot_book_with_a_closed_provider() -> None:
    closed = Provider(
        id="chen",
        name="Doctor Chen",
        specialty="Family Medicine",
        accepting_new_patients=False,
    )
    slot = Slot(provider_id="chen", start=datetime(2026, 8, 18, 9, 30))
    records = Clinic(now=NOW, providers=[closed], slots=[slot])
    newcomer = records.register_patient(
        first_name="Shayne",
        last_name="Parlo",
        date_of_birth=date(1989, 8, 1),
    )

    with pytest.raises(ProviderEligibilityError):
        records.book(
            patient=newcomer,
            slot_id=slot.id,
            visit_type="sick_visit",
        )


def test_children_cannot_book_an_adult_panel() -> None:
    adult = Provider(
        id="alvarez",
        name="Doctor Alvarez",
        specialty="Family Medicine",
        panel=ProviderPanel.ADULT,
    )
    slot = Slot(provider_id="alvarez", start=datetime(2026, 8, 18, 9, 30))
    child = Patient(
        chart_id="MRN2",
        first_name="Theo",
        last_name="Whitaker",
        date_of_birth=date(2019, 11, 5),
    )
    records = Clinic(now=NOW, providers=[adult], patients=[child], slots=[slot])

    with pytest.raises(ProviderEligibilityError):
        records.book(patient=child, slot_id=slot.id, visit_type="well_child")


def test_registration_insurance_messages_and_intake_are_plain_records() -> None:
    records = clinic()
    newcomer = records.register_patient(
        first_name="Shayne",
        last_name="Parlo",
        date_of_birth=date(1989, 8, 1),
        phone="5550188",
    )
    records.record_insurance(
        newcomer, Insurance(carrier="Meridian Choice", member_id="MC123")
    )
    records.take_message(
        kind="nurse_callback", chart_id=newcomer.chart_id, summary="foot pain"
    )
    intake = records.intake_for(newcomer.chart_id)
    intake.chief_complaint = "foot pain"
    intake.symptom_duration = "three days"
    intake.medications = []
    intake.allergies = []
    intake.conditions = []
    intake.pharmacy = "none"
    intake.complete()

    assert newcomer.registered_on_this_call
    assert newcomer.insurance and newcomer.insurance.carrier == "Meridian Choice"
    assert records.messages[0].kind == "nurse_callback"
    assert intake.disposition.value == "completed"


def test_the_live_clinic_is_fresh_and_uses_weekday_slots() -> None:
    first = open_clinic(NOW)
    second = open_clinic(NOW)
    first.patients[0].first_name = "Changed"

    assert second.patients[0].first_name != "Changed"
    assert first.open_slots()
    assert all(slot.start.weekday() < 5 for slot in first.open_slots())


def test_existing_appointments_are_removed_from_open_slots() -> None:
    slot = Slot(provider_id="alvarez", start=datetime(2026, 8, 18, 9, 30))
    appointment = Appointment(
        id="APT1",
        chart_id="MRN1",
        provider_id=slot.provider_id,
        start=slot.start,
        visit_type="follow_up",
    )
    records = Clinic(
        now=NOW,
        providers=[
            Provider(
                id="alvarez",
                name="Doctor Alvarez",
                specialty="Family Medicine",
            )
        ],
        patients=[patient()],
        slots=[slot],
        appointments=[appointment],
    )

    assert records.open_slots() == []
