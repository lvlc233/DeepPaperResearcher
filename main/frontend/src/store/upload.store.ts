import { create } from 'zustand';

type UploadOpenArg =
  | (() => void)
  | {
      onSuccess?: () => void;
      collectionId?: string | null;
    };

interface UploadStore {
  isOpen: boolean;
  collectionId: string | null;
  onUploadSuccess?: () => void;
  lastUploadTime: number; // For subscribers to detect changes
  setCollectionId: (collectionId: string | null) => void;
  open: (arg?: UploadOpenArg) => void;
  close: () => void;
  triggerSuccess: () => void;
}

export const useUploadStore = create<UploadStore>((set, get) => ({
  isOpen: false,
  collectionId: null,
  onUploadSuccess: undefined,
  lastUploadTime: 0,
  setCollectionId: (collectionId) => set({ collectionId }),
  open: (arg) => {
    if (typeof arg === 'function') {
      set({ isOpen: true, onUploadSuccess: arg });
      return;
    }

    const hasCollectionId = !!arg && Object.prototype.hasOwnProperty.call(arg, 'collectionId');

    set({
      isOpen: true,
      onUploadSuccess: arg?.onSuccess,
      ...(hasCollectionId ? { collectionId: arg?.collectionId ?? null } : {}),
    });
  },
  close: () => set({ isOpen: false, onUploadSuccess: undefined }),
  triggerSuccess: () => {
      const state = get();
      if (state.onUploadSuccess) {
          state.onUploadSuccess();
      }
      set({ lastUploadTime: Date.now() });
  }
}));
