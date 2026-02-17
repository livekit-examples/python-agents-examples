import { getJobContext, llm, voice } from '@livekit/agents';
import { z } from 'zod';

const VALID_FIELD_NAMES = [
  'fullName',
  'dob',
  'address',
  'phone',
  'emergencyName',
  'emergencyRelationship',
  'emergencyPhone',
  'medications',
  'allergies',
  'reasonForVisit',
] as const;

function getRemoteParticipantIdentity(): string {
  const room = getJobContext().room;
  const participant = Array.from(room.remoteParticipants.values()).find(
    (p) => !p.identity.startsWith('anam-')
  );
  if (!participant) {
    throw new llm.ToolError('No remote participant found');
  }
  return participant.identity;
}

async function performRpcToFrontend(
  method: string,
  payload: string
): Promise<string> {
  const room = getJobContext().room;
  const localParticipant = room.localParticipant;
  if (!localParticipant) {
    throw new llm.ToolError('Agent not connected to room');
  }
  const destinationIdentity = getRemoteParticipantIdentity();
  return localParticipant.performRpc({
    destinationIdentity,
    method,
    payload,
    responseTimeout: 5000,
  });
}

const updateField = llm.tool({
  description:
    'Update a form field on the patient intake form. Use this when the patient provides information for a specific field.',
  parameters: z.object({
    fieldName: z
      .string()
      .describe(
        'The field ID to update: fullName, dob, address, phone, emergencyName, emergencyRelationship, emergencyPhone, medications, allergies, reasonForVisit'
      ),
    value: z.string().describe('The value to set for the field'),
  }),
  execute: async ({ fieldName, value }) => {
    if (!VALID_FIELD_NAMES.includes(fieldName as (typeof VALID_FIELD_NAMES)[number])) {
      throw new llm.ToolError(`Invalid field name: ${fieldName}`);
    }
    try {
      const response = await performRpcToFrontend(
        'updateField',
        JSON.stringify({ fieldName, value })
      );
      return response;
    } catch (error) {
      throw new llm.ToolError(`Failed to update field: ${String(error)}`);
    }
  },
});

const getFormState = llm.tool({
  description:
    'Get the current state of all form fields. Use this to see what has already been filled in or to verify data before submitting.',
  execute: async () => {
    try {
      const response = await performRpcToFrontend('getFormState', '{}');
      return response;
    } catch (error) {
      throw new llm.ToolError(`Failed to get form state: ${String(error)}`);
    }
  },
});

const submitForm = llm.tool({
  description:
    'Submit the completed intake form. Use this only when all required fields have been filled and the patient has confirmed they are ready to submit.',
  execute: async (_params, { ctx }) => {
    try {
      const response = await performRpcToFrontend('submitForm', '{}');
      ctx.session.say(
        'Your form has been submitted. You will be contacted soon. Thank you.'
      );
      return response;
    } catch (error) {
      throw new llm.ToolError(`Failed to submit form: ${String(error)}`);
    }
  },
});

export class Agent extends voice.Agent {
  constructor() {
    super({
      instructions: `You are Liv, a voice AI intake assistant powered by LiveKit and Anam. You help patients complete an intake form one section at a time in a calm, clear, supportive tone.

      Conversation style:
      - Speak in short, natural sentences.
      - Be warm and professional.
      - Keep the user moving forward without rushing them.
      - Do not use markdown, emojis, asterisks, or stage directions.

      Intake flow (in order):
      1) full legal name
      2) date of birth
      3) current home address
      4) best phone number
      5) emergency contact name, relationship, and phone
      6) current medications
      7) medication allergies (allow "unknown" if unsure)
      8) reason for visit in the patient's own words
      9) final confirmation loop and submission

      Confirmation rules:
      - Confirm each answer before moving to the next field.
      - For names and medication names, read back with spelling when helpful (for example: "Is that J-E-S-S-E H-A-L-L?" or "Is that Metformin, M-E-T-F-O-R-M-I-N?").
      - If user says "yes," proceed. If user corrects, update and confirm once more.
      - If user is unsure, offer to mark unknown or come back later.

      Tool usage:
      - Use update_field whenever the user provides a value for a form field.
      - Keep frontend field names exact:
        fullName, dob, address, phone, emergencyName, emergencyRelationship, emergencyPhone, medications, allergies, reasonForVisit.
      - Use get_form_state before the final confirmation if needed to verify current values.
      - At the end, ask the patient to confirm whether all entries are accurate.
      - If the patient says yes, submit the form.
      - If the patient says no and asks to change something, update the requested field(s), then ask for confirmation again.
      - Repeat this confirmation loop until the patient explicitly confirms all entries are accurate, then submit.
      - The submit_form tool speaks the final confirmation; do not add your own.

      Opening:
      Start with: "Hi, I'm a voice AI avatar powered by LiveKit and Anam, here to help you fill out your intake form today. We'll go through it together, one section at a time. Let's start with some basic information."
      Then ask for the patient's full name.`,

      tools: {
        update_field: updateField,
        get_form_state: getFormState,
        submit_form: submitForm,
      },
    });
  }
}
