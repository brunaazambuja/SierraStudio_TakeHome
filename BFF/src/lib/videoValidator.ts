export interface ValidationConfig {
  maxSizeMB: number;
  allowedMimeTypes: string[];
  allowedExtensions: string[];
}

export interface ValidationResult {
  valid: boolean;
  error?: string;
  details?: {
    size: number;
    mimeType: string;
    extension: string;
  };
}

const DEFAULT_CONFIG: ValidationConfig = {
  maxSizeMB: 1000,
  allowedMimeTypes: ['video/mp4', 'video/quicktime', 'video/webm'],
  allowedExtensions: ['.mp4', '.mov', '.webm'],
};

function validateType(filename: string, mimetype: string): ValidationResult {
  const mimeValid = DEFAULT_CONFIG.allowedMimeTypes.some(
    (allowed) =>
      mimetype.toLowerCase() === allowed.toLowerCase() ||
      mimetype.toLowerCase().startsWith('video/')
  );

  if (!mimeValid) {
    return {
      valid: false,
      error: `Invalid video type: ${mimetype}`,
    };
  }

  const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
  const extValid = DEFAULT_CONFIG.allowedExtensions.some(
    (allowed) => extension === allowed.toLowerCase()
  );

  if (!extValid) {
    return {
      valid: false,
      error: `Invalid file extension: ${extension}`,
    };
  }

  return { valid: true };
}

function validateSize(sizeBytes: number): ValidationResult {
  const sizeMB = sizeBytes / (1024 * 1024);

  if (sizeBytes === 0) {
    return { valid: false, error: 'Video file is empty' };
  }

  if (sizeMB > DEFAULT_CONFIG.maxSizeMB) {
    return {
      valid: false,
      error: `Video file too large: ${sizeMB.toFixed(2)}MB. Maximum allowed: 1GB`,
    };
  }

  return { valid: true };
}

export async function validate(
  buffer: Buffer,
  filename: string,
  mimetype: string
): Promise<ValidationResult> {
  const typeValidation = validateType(filename, mimetype);
  if (!typeValidation.valid) return typeValidation;
  const sizeValidation = validateSize(buffer.length);
  if (!sizeValidation.valid) return sizeValidation;

  const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
  return {
    valid: true,
    details: {
      size: buffer.length,
      mimeType: mimetype,
      extension,
    },
  };
}
