import { Request, Response } from "express";
import { deleteVideo, getAllVideos, getVideoStream, uploadVideo } from "../lib/videos";

export const listVideos = async (req: Request, res: Response) => {
	try {
		const videos = await getAllVideos();
		return res.status(200).json(videos);
	} catch (e) {
		const message = `Failed to fetch videos`;
		console.error(message, e);
		return res.status(500).json({ message: `${(e as Error).message}` });
	}
};

export const streamVideo = async (req: Request, res: Response) => {
	const { videoName } = req.params;
	const { resolution = "720p" } = req.query;

	try {
		if (!videoName) {
			return res.status(400).json({ message: "Video name is required" });
		}

		const stream = await getVideoStream(videoName, resolution as string);

		res.setHeader("Content-Type", "video/mp4");
		res.setHeader("Accept-Ranges", "bytes");

		stream.pipe(res);
	} catch (e) {
		const message = `Failed to stream video`;
		console.error(message, e);
		return res.status(500).json({ message: `${(e as Error).message}` });
	}
};

export const uploadVideoHandler = async (req: Request, res: Response) => {
	const { title } = req.body;
	const file = req.file;

	if (!title || !file) {
		return res.status(400).json({ message: "Title and video file are required" });
	}

	try {
		const result = await uploadVideo(title, file);

		return res.status(200).json({
			result,
		});
	} catch (e) {
		const message = `Failed to upload video`;
		console.error(message, e);
		return res.status(500).json({ message: `${(e as Error).message}` });
	}
};

export const deleteVideoHandler = async (req: Request, res: Response) => {
	const { videoName } = req.params;

	try {
		if (!videoName) {
			return res.status(400).json({ message: "Video name is required" });
		}

		await deleteVideo(videoName);
		return res.status(200).json({
			success: true,
			message: `Video '${videoName}' deleted successfully`,
		});
	} catch (e) {
		const message = `Failed to delete video`;
		console.error(message, e);
		return res.status(500).json({ message: `${(e as Error).message}` });
	}
};
