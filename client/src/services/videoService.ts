import api from "./api";

export interface Video {
	base_name: string;
	display_name: string;
	size: number;
	last_modified: string;
	resolutions: string[];
	poster_url?: string | null;
	thumbnail_strip_url?: string | null;
}

export const videoService = {
	async getAllVideos(): Promise<Video[]> {
		const response = await api.get("/videos");
		return response.data;
	},

	async deleteVideo(videoName: string): Promise<void> {
		await api.delete(`/videos/${encodeURIComponent(videoName)}`);
	},

	async uploadVideo(title: string, file: File, onProgress?: (progress: number) => void): Promise<void> {
		const formData = new FormData();
		formData.append("title", title);
		formData.append("video_file", file);

		return await api.post("/upload", formData, {
			headers: {
				"Content-Type": "multipart/form-data",
			},
			onUploadProgress: (progressEvent) => {
				if (progressEvent.total && onProgress) {
					const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
					onProgress(progress);
				}
			},
		});
	},

	getVideoUrl(videoName: string, resolution: string = "720p"): string {
		return `${api.defaults.baseURL}/videos/${encodeURIComponent(videoName)}?resolution=${resolution}`;
	},
};
