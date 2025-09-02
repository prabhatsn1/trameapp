"use client";

import React, { useState } from "react";
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  Card,
  CardContent,
  CardActions,
  Divider,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  CloudUpload,
  Description,
  Launch,
  Refresh,
  ThreeDRotation,
  Code,
  Terminal,
} from "@mui/icons-material";
import Papa from "papaparse";

interface CSVData {
  headers: string[];
  rows: string[][];
}

export default function Home() {
  const [csvData, setCsvData] = useState<CSVData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>("");
  const [trameServerRunning, setTrameServerRunning] = useState(false);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== "text/csv" && !file.name.endsWith(".csv")) {
      setError("Please upload a valid CSV file");
      return;
    }

    setLoading(true);
    setError(null);
    setFileName(file.name);

    Papa.parse(file, {
      complete: (results) => {
        if (results.errors.length > 0) {
          setError("Error parsing CSV file");
          setLoading(false);
          return;
        }

        const data = results.data as string[][];
        if (data.length === 0) {
          setError("CSV file is empty");
          setLoading(false);
          return;
        }

        const headers = data[0];
        const rows = data
          .slice(1)
          .filter((row) => row.some((cell) => cell.trim() !== ""));

        setCsvData({ headers, rows });
        setLoading(false);
      },
      header: false,
      skipEmptyLines: true,
    });
  };

  const clearData = () => {
    setCsvData(null);
    setFileName("");
    setError(null);
  };

  const has3DColumns = (data: CSVData) => {
    const requiredColumns = [
      "x",
      "y",
      "z",
      "componentId",
      "MaterialId",
      "True_Temp",
      "Pred_Temp",
      "Abs_Error",
    ];
    return requiredColumns.every((col) =>
      data.headers.some((header) => header.toLowerCase() === col.toLowerCase())
    );
  };

  const checkTrameServer = async () => {
    try {
      const response = await fetch("http://localhost:8080", { method: "HEAD" });
      setTrameServerRunning(response.ok);
    } catch {
      setTrameServerRunning(false);
    }
  };

  React.useEffect(() => {
    checkTrameServer();
    const interval = setInterval(checkTrameServer, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box textAlign="center" mb={4}>
        <Typography
          variant="h3"
          component="h1"
          gutterBottom
          sx={{ fontWeight: 300 }}
        >
          CSV 3D Data Visualizer
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Upload CSV files and visualize 3D data with interactive controls
        </Typography>
      </Box>

      <Stack
        direction={{ xs: "column", lg: "row" }}
        spacing={4}
        sx={{ minHeight: "70vh" }}
      >
        {/* CSV Upload and Preview Section */}
        <Stack flex={1} spacing={4}>
          <Paper elevation={2} sx={{ p: 4 }}>
            <Typography
              variant="h5"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              <Description /> CSV Data
            </Typography>

            <Box textAlign="center">
              <input
                accept=".csv"
                style={{ display: "none" }}
                id="csv-upload"
                type="file"
                onChange={handleFileUpload}
              />
              <label htmlFor="csv-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<CloudUpload />}
                  size="large"
                  sx={{ mb: 2 }}
                  disabled={loading}
                >
                  {loading ? "Processing..." : "Upload CSV File"}
                </Button>
              </label>

              {loading && (
                <Box mt={2}>
                  <CircularProgress size={24} />
                </Box>
              )}

              {fileName && !loading && (
                <Box mt={2}>
                  <Chip
                    icon={<Description />}
                    label={fileName}
                    color="primary"
                    variant="outlined"
                    onDelete={clearData}
                  />
                </Box>
              )}

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              {csvData && has3DColumns(csvData) && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <ThreeDRotation />
                    3D visualization compatible! Use the Trame Visualizer to
                    explore your data.
                  </Box>
                </Alert>
              )}
            </Box>
          </Paper>

          {csvData && (
            <Paper elevation={2} sx={{ p: 4, flex: 1 }}>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                mb={3}
              >
                <Typography variant="h6" component="h2">
                  CSV Preview
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {csvData.rows.length} rows • {csvData.headers.length} columns
                </Typography>
              </Box>

              <TableContainer sx={{ maxHeight: 400 }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      {csvData.headers.map((header, index) => (
                        <TableCell
                          key={index}
                          sx={{
                            fontWeight: "bold",
                            backgroundColor: "primary.main",
                            color: "primary.contrastText",
                          }}
                        >
                          {header}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {csvData.rows.slice(0, 100).map((row, rowIndex) => (
                      <TableRow
                        key={rowIndex}
                        sx={{
                          "&:nth-of-type(odd)": {
                            backgroundColor: "action.hover",
                          },
                        }}
                      >
                        {row.map((cell, cellIndex) => (
                          <TableCell key={cellIndex}>{cell}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {csvData.rows.length > 100 && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 1, display: "block" }}
                >
                  Showing first 100 rows of {csvData.rows.length} total rows
                </Typography>
              )}
            </Paper>
          )}
        </Stack>

        {/* 3D Visualization Section */}
        <Stack flex={1} spacing={4}>
          <Paper elevation={2} sx={{ p: 4 }}>
            <Typography
              variant="h5"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              <ThreeDRotation /> 3D Visualization
            </Typography>

            <Stack spacing={2}>
              <Box display="flex" alignItems="center" gap={2}>
                <Typography variant="body2">Trame Server Status:</Typography>
                <Chip
                  label={trameServerRunning ? "Running" : "Stopped"}
                  color={trameServerRunning ? "success" : "error"}
                  size="small"
                />
                <Tooltip title="Refresh status">
                  <IconButton size="small" onClick={checkTrameServer}>
                    <Refresh />
                  </IconButton>
                </Tooltip>
              </Box>

              {trameServerRunning ? (
                <Alert severity="success">
                  <Box
                    display="flex"
                    alignItems="center"
                    justifyContent="space-between"
                  >
                    <span>3D Visualizer is ready!</span>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<Launch />}
                      href="http://localhost:8080"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Open Visualizer
                    </Button>
                  </Box>
                </Alert>
              ) : (
                <Alert severity="warning">
                  Start the Python backend to enable 3D visualization
                </Alert>
              )}
            </Stack>

            {/* Embedded Visualizer (when server is running) */}
            {trameServerRunning && (
              <Card variant="outlined" sx={{ mt: 3 }}>
                <CardContent sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Live 3D Visualization
                  </Typography>
                  <Box
                    sx={{
                      width: "100%",
                      height: 500,
                      border: "1px solid",
                      borderColor: "divider",
                      borderRadius: 1,
                      overflow: "hidden",
                    }}
                  >
                    <iframe
                      src="http://localhost:8080"
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      title="Trame 3D Visualizer"
                      style={{ border: "none" }}
                    />
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<Launch />}
                    href="http://localhost:8080"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open in New Tab
                  </Button>
                </CardActions>
              </Card>
            )}
          </Paper>

          {/* Python Backend Instructions */}
          <Paper elevation={2} sx={{ p: 4 }}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              <Terminal /> Python Backend Setup
            </Typography>

            <Typography variant="body2" color="text.secondary" paragraph>
              Follow these steps to start the 3D visualization server:
            </Typography>

            <Stack spacing={2}>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Quick Start:</strong> Run the startup script
                </Typography>
                <Paper
                  variant="outlined"
                  sx={{ p: 2, backgroundColor: "grey.50" }}
                >
                  <Typography
                    variant="body2"
                    component="code"
                    sx={{ fontFamily: "monospace" }}
                  >
                    ./start_visualizer.sh
                  </Typography>
                </Paper>
              </Box>

              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Manual Setup:</strong> If you prefer manual
                  installation
                </Typography>
                <Paper
                  variant="outlined"
                  sx={{ p: 2, backgroundColor: "grey.50" }}
                >
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      fontFamily: "monospace",
                      whiteSpace: "pre-wrap",
                    }}
                  >{`# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python trame_visualizer.py`}</Typography>
                </Paper>
              </Box>
            </Stack>

            <Divider sx={{ my: 2 }} />

            <Typography variant="body2" color="text.secondary" paragraph>
              <strong>Required CSV Columns for 3D Visualization:</strong>
            </Typography>

            <Stack spacing={0.5}>
              <Typography variant="body2">
                • <code>x, y, z</code> - 3D coordinates
              </Typography>
              <Typography variant="body2">
                • <code>componentId</code> - Component filter
              </Typography>
              <Typography variant="body2">
                • <code>MaterialId</code> - Material filter
              </Typography>
              <Typography variant="body2">
                • <code>True_Temp, Pred_Temp, Abs_Error</code> - Color mapping
                values
              </Typography>
            </Stack>

            <Box mt={3}>
              <Button
                variant="outlined"
                startIcon={<Code />}
                href="https://kitware.github.io/trame/"
                target="_blank"
                rel="noopener noreferrer"
                size="small"
              >
                Learn More About Trame
              </Button>
            </Box>
          </Paper>
        </Stack>
      </Stack>
    </Container>
  );
}
