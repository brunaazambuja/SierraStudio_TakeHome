import FormData from "form-data";
import { fastAPIClient } from "../api/fastApi";
import { validate } from "./videoValidator";

export interface Video {
	base_name: string;
	display_name: string;
	size: number;
	last_modified: string;
	resolutions: string[];
	poster_url?: string | null;
	thumbnail_strip_url?: string | null;
}

export const getAllVideos = async (): Promise<Video[]> => {
	try {
		const response = await fastAPIClient.get("/videos");
		return response.data;
	} catch (error) {
		console.error("Error fetching videos:", error);
		throw new Error("Failed to fetch videos from FastAPI");
	}
};

export const getVideoStream = async (videoName: string, resolution: string = "720p") => {
	try {
		const response = await fastAPIClient.get(`/videos/${videoName}`, {
			params: { resolution },
			responseType: "stream",
		});
		return response.data;
	} catch (error) {
		console.error("Error streaming video:", error);
		throw new Error("Failed to stream video from FastAPI");
	}
};

export const uploadVideo = async (
	title: string,
	file: Express.Multer.File
): Promise<{ message: string; data?: any }> => {
	try {
		const fileBuffer = file.buffer;
		const filename = file.originalname;
		const mimetype = file.mimetype;

		const formData = new FormData();
		formData.append("title", title);
		formData.append("video_file", fileBuffer, {
			filename: filename,
			contentType: mimetype,
		});

		console.log(
			`Validating video: ${file.originalname} (${file.mimetype}, ${(file.size / (1024 * 1024)).toFixed(2)}MB)`
		);

		const validationResult = await validate(file.buffer, file.originalname, file.mimetype);

		if (!validationResult.valid) {
			console.log(`Video validation failed: ${validationResult.error}`);
			throw new Error(validationResult.error);
		}

		console.log("Video validation passed:", validationResult.details);

		const response = await fastAPIClient.post<{ message?: string; data?: any; error?: boolean }>("/upload", formData, {
			headers: {
				...formData.getHeaders(),
			},
			maxContentLength: Infinity,
			maxBodyLength: Infinity,
		});

		if (response.data.error) {
			throw new Error(response.data.message);
		}

		return {
			data: response.data,
			message: response.data?.message || "Video uploaded successfully",
		};
	} catch (error: any) {
		console.error("Error uploading video:", error.response?.data || error.message);
		throw new Error(error.response?.data || error.message || "Failed to upload video to FastAPI");
	}
};

export const deleteVideo = async (videoName: string): Promise<void> => {
	try {
		await fastAPIClient.delete(`/videos/${videoName}`);
	} catch (error: any) {
		console.error("Error deleting video:", error);
		throw new Error(error.response?.data?.detail || "Failed to delete video from FastAPI");
	}
};
