export const INTAKE_FIELD_IDS = [
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

export type IntakeFieldId = (typeof INTAKE_FIELD_IDS)[number];

export interface IntakeFormData {
  fullName: string;
  dob: string;
  address: string;
  phone: string;
  emergencyName: string;
  emergencyRelationship: string;
  emergencyPhone: string;
  medications: string;
  allergies: string;
  reasonForVisit: string;
}

export const EMPTY_FORM_DATA: IntakeFormData = {
  fullName: '',
  dob: '',
  address: '',
  phone: '',
  emergencyName: '',
  emergencyRelationship: '',
  emergencyPhone: '',
  medications: '',
  allergies: '',
  reasonForVisit: '',
};

export function isValidFieldName(name: string): name is IntakeFieldId {
  return INTAKE_FIELD_IDS.includes(name as IntakeFieldId);
}
