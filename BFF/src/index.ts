import { app } from './app';

const PORT = process.env.PORT;

app.listen(PORT, () =>
  console.log(
    `⚡️[BFF]: Server is running at http://localhost:${PORT}`
  )
);
