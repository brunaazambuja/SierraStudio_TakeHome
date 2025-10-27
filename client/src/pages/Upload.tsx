import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { Box, Button, CircularProgress, LinearProgress, Paper, TextField, Typography } from "@mui/material";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../context/ToastContext";
import { videoService } from "../services/videoService";

export default function Upload() {
	const [title, setTitle] = useState("");
	const [file, setFile] = useState<File | null>(null);
	const [uploading, setUploading] = useState(false);
	const [progress, setProgress] = useState(0);
	const navigate = useNavigate();
	const { showToast } = useToast();
	const abortControllerRef = useRef<AbortController | null>(null);

	const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		if (e.target.files && e.target.files[0]) {
			setFile(e.target.files[0]);
		}
	};

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!title || !file) {
			showToast("Please provide both title and video file", "error");
			return;
		}

		try {
			setUploading(true);
			setProgress(0);

			await videoService.uploadVideo(title, file, (prog) => {
				setProgress(prog);
			});

			showToast("Video uploaded successfully!", "success");
			navigate("/");
		} catch (err: any) {
			showToast(`Failed to upload video: ${err.response.data.message}`, "error");
			console.error("Upload error:", err);
		} finally {
			setUploading(false);
			setProgress(0);
			abortControllerRef.current = null;
		}
	};

	return (
		<>
			<Typography variant="h4" component="h2" gutterBottom>
				Upload Video
			</Typography>

			<Paper sx={{ p: 4, mt: 3, maxWidth: 600 }}>
				<Box component="form" onSubmit={handleSubmit}>
					<TextField
						fullWidth
						label="Video Title"
						value={title}
						onChange={(e) => setTitle(e.target.value)}
						required
						disabled={uploading}
						sx={{ mb: 3 }}
					/>

					<Button
						variant="outlined"
						component="label"
						fullWidth
						startIcon={<CloudUploadIcon />}
						disabled={uploading}
						sx={{ mb: 2 }}>
						{file ? file.name : "Select Video"}
						<input type="file" hidden accept="video/*" onChange={handleFileChange} required />
					</Button>

					{uploading && progress < 100 && (
						<Box sx={{ width: "100%", mb: 2 }}>
							<LinearProgress variant="determinate" value={progress} />
							<Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
								{progress}% uploaded
							</Typography>
						</Box>
					)}

					{uploading && progress === 100 && (
						<Box
							sx={{
								width: "100%",
								mb: 2,
								display: "flex",
								flexDirection: "column",
								alignItems: "center",
							}}>
							<CircularProgress />
							<Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
								Video uploaded successfully! Processing transcoding for different resolutions... Your video will be
								available in a few minutes on the home page.
							</Typography>
						</Box>
					)}

					<Button type="submit" variant="contained" fullWidth disabled={uploading || !title || !file}>
						{uploading ? "Uploading..." : "Upload"}
					</Button>
				</Box>
			</Paper>
		</>
	);
}
