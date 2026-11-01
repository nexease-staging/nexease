import { Capacitor } from '@capacitor/core';
import { Filesystem, Directory } from '@capacitor/filesystem';
import { Share } from '@capacitor/share';

export async function downloadBlob(blob: Blob, filename: string): Promise<void> {
  const safeName = filename.replace(/[^a-zA-Z0-9._-]/g, '_').slice(-160) || 'NexEase-export';
  if (Capacitor.isNativePlatform()) {
    const data = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(',')[1]);
      reader.onerror = () => reject(new Error('Unable to prepare the document.'));
      reader.readAsDataURL(blob);
    });
    const path = `nexease-share/${Date.now()}-${safeName}`;
    const file = await Filesystem.writeFile({ path, data, directory: Directory.Cache, recursive: true });
    await Share.share({ title: filename, files: [file.uri], dialogTitle: 'Save or share your NexEase document' });
    return;
  }
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url; anchor.download = safeName;
  document.body.appendChild(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

export async function clearOldShareFiles(): Promise<void> {
  if (!Capacitor.isNativePlatform()) return;
  const listing = await Filesystem.readdir({ path: 'nexease-share', directory: Directory.Cache }).catch(() => ({ files: [] }));
  for (const file of listing.files) {
    const created = Number(file.name.split('-')[0]);
    if (created > 0 && Date.now() - created > 86400000) {
      await Filesystem.deleteFile({ path: `nexease-share/${file.name}`, directory: Directory.Cache }).catch(() => undefined);
    }
  }
}
