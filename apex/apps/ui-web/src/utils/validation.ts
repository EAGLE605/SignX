import type { Stage } from '../store/projectStore';

export interface StageValidation {
  isValid: boolean;
  errors: string[];
}

export function validateStage(stage: Stage, projectData: Record<string, unknown>): StageValidation {
  const errors: string[] = [];

  switch (stage) {
    case 'site':
      if (!projectData.site?.address && !projectData.site?.latitude) {
        errors.push('Site location must be resolved');
      }
      break;

    case 'cabinet': {
      const cab = projectData.cabinet;
      if (!cab || !cab.width_in || !cab.height_in || !cab.depth_in || !cab.density_lb_ft3) {
        errors.push('Cabinet dimensions and density are required');
      }
      if (cab && (cab.width_in <= 0 || cab.height_in <= 0 || cab.depth_in <= 0 || cab.density_lb_ft3 <= 0)) {
        errors.push('All cabinet values must be positive');
      }
      break;
    }

    case 'structural':
      if (!projectData.structural?.pole_shape || !projectData.structural?.pole_size) {
        errors.push('Pole selection is required');
      }
      break;

    case 'foundation':
      if (!projectData.foundation?.type) {
        errors.push('Foundation type must be selected');
      }
      if (projectData.foundation?.type === 'direct_burial' && !projectData.foundation?.diameter_in) {
        errors.push('Foundation diameter is required');
      }
      break;

    case 'finalization':
      if (!projectData.pricing?.total) {
        errors.push('Pricing estimate is required');
      }
      break;

    default:
      // Overview, review, submission don't require validation
      break;
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}
