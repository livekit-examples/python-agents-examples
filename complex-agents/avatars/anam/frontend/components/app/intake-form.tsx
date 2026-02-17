'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { type IntakeFormData } from '@/lib/form-fields';
import { cn } from '@/lib/shadcn/utils';

interface IntakeFormProps {
  formData: IntakeFormData;
  onFormDataChange: (data: IntakeFormData) => void;
  isSubmitted: boolean;
  onSubmit: () => void;
  className?: string;
}

export function IntakeForm({
  formData,
  onFormDataChange,
  isSubmitted,
  onSubmit,
  className,
}: IntakeFormProps) {
  const updateField = (field: keyof IntakeFormData, value: string) => {
    onFormDataChange({ ...formData, [field]: value });
  };
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  if (isSubmitted) {
    return (
      <div className={cn('flex flex-col items-center justify-center gap-4 py-12', className)}>
        <div className="bg-primary/20 flex size-16 items-center justify-center rounded-full">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <p className="text-lg font-medium">Form submitted</p>
        <p className="text-muted-foreground text-sm">Thank you for completing your intake form.</p>
      </div>
    );
  }

  return (
    <form
      className={cn('space-y-6 overflow-y-auto p-6 pb-24 md:pb-6', className)}
      onSubmit={handleSubmit}
    >
      <div className="space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">Patient intake form</h2>
        <p className="text-muted-foreground text-sm">
          Let our AI assistant guide you through the intake process.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Personal info</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fullName">Full name</Label>
            <Input
              id="fullName"
              value={formData.fullName}
              onChange={(e) => updateField('fullName', e.target.value)}
              placeholder="Legal name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="dob">Date of birth</Label>
            <Input
              id="dob"
              value={formData.dob}
              onChange={(e) => updateField('dob', e.target.value)}
              placeholder="MM/DD/YYYY"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">Address</Label>
            <Input
              id="address"
              value={formData.address}
              onChange={(e) => updateField('address', e.target.value)}
              placeholder="Street address"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone number</Label>
            <Input
              id="phone"
              value={formData.phone}
              onChange={(e) => updateField('phone', e.target.value)}
              placeholder="(555) 123-4567"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Emergency contact</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="emergencyName">Contact name</Label>
            <Input
              id="emergencyName"
              value={formData.emergencyName}
              onChange={(e) => updateField('emergencyName', e.target.value)}
              placeholder="Name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="emergencyRelationship">Relationship</Label>
            <Input
              id="emergencyRelationship"
              value={formData.emergencyRelationship}
              onChange={(e) => updateField('emergencyRelationship', e.target.value)}
              placeholder="e.g. Spouse, Parent"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="emergencyPhone">Contact phone</Label>
            <Input
              id="emergencyPhone"
              value={formData.emergencyPhone}
              onChange={(e) => updateField('emergencyPhone', e.target.value)}
              placeholder="(555) 123-4567"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Medical history</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="medications">Current medications</Label>
            <Textarea
              id="medications"
              value={formData.medications}
              onChange={(e) => updateField('medications', e.target.value)}
              placeholder="List any medications you are currently taking"
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="allergies">Allergies</Label>
            <Textarea
              id="allergies"
              value={formData.allergies}
              onChange={(e) => updateField('allergies', e.target.value)}
              placeholder="List any known allergies"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Reason for visit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="reasonForVisit">Description</Label>
            <Textarea
              id="reasonForVisit"
              value={formData.reasonForVisit}
              onChange={(e) => updateField('reasonForVisit', e.target.value)}
              placeholder="Describe the reason for your visit"
              rows={4}
            />
          </div>
        </CardContent>
      </Card>

      <Button
        type="submit"
        id="submit-intake-form"
        data-testid="submit-intake-form"
        aria-label="Submit intake form"
        className="w-full"
        size="lg"
      >
        Submit
      </Button>
    </form>
  );
}
