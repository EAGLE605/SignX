// Legacy envelope type - use types/envelope.ts for full type
export interface ResponseEnvelope<T = unknown> {
  result: T | null;
  assumptions: string[];
  confidence: number;
  trace: {
    data: {
      inputs: Record<string, unknown>;
      intermediates: Record<string, unknown>;
      outputs: Record<string, unknown>;
    };
    code_version: {
      git_sha: string;
      dirty: boolean;
      build_id?: string;
    };
    model_config: {
      provider: string;
      model: string;
      temperature: number;
      max_tokens: number;
      seed?: number | null;
    };
  };
}

// Re-export full envelope type
export type { ResponseEnvelope as FullEnvelope } from './envelope';

export interface Project {
  id: string;
  name: string;
  notes?: string;
  status: 'draft' | 'estimating' | 'submitted' | 'accepted' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface SiteResolveRequest {
  address: string;
}

export interface SiteResolveResponse {
  latitude: number;
  longitude: number;
  wind_speed_mph: number;
  snow_load_psf?: number;
  exposure: 'B' | 'C' | 'D';
  address?: string;
  zip_code?: string;
}

export interface CabinetDeriveRequest {
  width_in: number;
  height_in: number;
  depth_in: number;
  density_lb_ft3: number;
}

export interface CabinetDeriveResponse {
  area_ft2?: number; // May be A_ft2 from API
  A_ft2?: number;
  volume_ft3?: number;
  weight_lb?: number;
  weight_estimate_lb?: number;
  center_of_gravity_in?: {
    x: number;
    y: number;
    z: number;
  };
  z_cg_ft?: number;
}

export interface PoleOptionsRequest {
  moment_required_ft_lb: number;
  material?: 'steel' | 'aluminum';
  height_ft?: number;
}

export interface PoleOption {
  shape: string;
  size: string;
  material: string;
  weight_lb_ft: number;
  section_modulus_in3: number;
  moment_capacity_ft_lb: number;
}

export interface PricingEstimateRequest {
  height_ft: number;
  addons?: string[];
}

export interface PricingEstimateResponse {
  project_id: string;
  version: string;
  items: Array<{ item: string; price: number }>;
  total: number;
}

export interface CanvasDimension {
  width: number;
  height: number;
  x: number;
  y: number;
}
