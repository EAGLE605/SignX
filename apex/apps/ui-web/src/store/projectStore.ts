import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { CanvasDimension } from '../types/api';

export type Stage =
  | 'overview'
  | 'site'
  | 'cabinet'
  | 'structural'
  | 'foundation'
  | 'finalization'
  | 'review'
  | 'submission';

export interface ProjectState {
  currentProjectId: string | null;
  currentStage: Stage;
  canvasDimensions: CanvasDimension | null;
  completedStages: Set<Stage>;
  projectData: {
    site?: {
      address?: string;
      latitude?: number;
      longitude?: number;
      wind_speed_mph?: number;
      exposure?: 'B' | 'C' | 'D';
    };
    cabinet?: {
      width_in: number;
      height_in: number;
      depth_in: number;
      density_lb_ft3: number;
    };
    structural?: {
      pole_shape?: string;
      pole_size?: string;
      moment_required_ft_lb?: number;
    };
    foundation?: {
      type?: 'direct_burial' | 'baseplate';
      diameter_in?: number;
      depth_ft?: number;
    };
    pricing?: {
      height_ft?: number;
      addons?: string[];
      total?: number;
    };
  };
  setCurrentProject: (id: string | null) => void;
  setCurrentStage: (stage: Stage) => void;
  markStageComplete: (stage: Stage) => void;
  setCanvasDimensions: (dimensions: CanvasDimension | null) => void;
  updateProjectData: (section: keyof ProjectState['projectData'], data: unknown) => void;
  resetProject: () => void;
}

const initialState = {
  currentProjectId: null,
  currentStage: 'overview' as Stage,
  canvasDimensions: null,
  completedStages: new Set<Stage>(),
  projectData: {},
};

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      ...initialState,
      setCurrentProject: (id) =>
        set({ currentProjectId: id }),
      setCurrentStage: (stage) =>
        set({ currentStage: stage }),
      markStageComplete: (stage) =>
        set((state) => ({
          completedStages: new Set([...state.completedStages, stage]),
        })),
      setCanvasDimensions: (dimensions) =>
        set({ canvasDimensions: dimensions }),
      updateProjectData: (section, data) =>
        set((state) => ({
          projectData: {
            ...state.projectData,
            [section]: data,
          },
        })),
      resetProject: () =>
        set(initialState),
    }),
    {
      name: 'apex-project-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentProjectId: state.currentProjectId,
        currentStage: state.currentStage,
        canvasDimensions: state.canvasDimensions,
        completedStages: Array.from(state.completedStages) as unknown as Set<Stage>,
        projectData: state.projectData,
      }),
      onRehydrateStorage: () => (state) => {
        if (state && Array.isArray(state.completedStages)) {
          state.completedStages = new Set(state.completedStages as Stage[]);
        }
      },
    },
  ),
);
