# simple_dashboard.py
# A simpler approach using Flask + Chart.js
# pip install flask pandas requests

from flask import Flask, render_template_string, jsonify
import pandas as pd
import requests
import json
import base64, os
from datetime import datetime

app = Flask(__name__)

# Your backend configuration
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyNvXaXuYO2q51Z7FhKWKXJx4BgM5Hqnz-lwebE9g5hRdvuJSRxKR3HuuqgZmXB3qqb/exec"
SECRET_KEY = "bS9xN4ZtJ2h8M0rQ5kV1pUeX6cYwA3fG7tLzB1nD4sM8qR9jP2yH6vE0oK7iW5u"

LOGO_FILE = "image.png"  # logo in same folder as this script

def get_logo_data_url(filename: str = LOGO_FILE) -> str:
    """Read image file and return data URL for embedding."""
    try:
        path = os.path.join(app.root_path, filename)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        ext = os.path.splitext(filename)[1].lower()
        mime = "image/png" if ext == ".png" else ("image/jpeg" if ext in (".jpg", ".jpeg") else "image/svg+xml")
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        print("Logo load error:", e)
        return ""

def fetch_data_from_backend(department):
    """Fetch data from your Google Apps Script backend"""
    try:
        params = {
            "action": "list_all",  # You may need to add this action to your backend
            "secret": SECRET_KEY,
            "department": department
        }
        response = requests.get(WEB_APP_URL, params=params, timeout=20)
        data = response.json()
        
        if data.get("ok"):
            return pd.DataFrame(data.get("records", []))
        else:
            print(f"Backend error: {data.get('error', 'Unknown error')}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def fetch_data_from_sheets(sheet_id, department):
    """Alternative: Fetch directly from Google Sheets CSV"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={department}"
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            # Parse CSV manually
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                return pd.DataFrame()
            
            headers = [h.strip('"') for h in lines[0].split(',')]
            data = []
            
            for line in lines[1:]:
                values = [v.strip('"') for v in line.split(',')]
                row = dict(zip(headers, values))
                data.append(row)
            
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching from sheets: {e}")
        return pd.DataFrame()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    logo_src = get_logo_data_url()
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Department Analytics Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: white;
            min-height: 100vh;
        }
        
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            position: relative;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #8b5cf6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Top-right logo and watermark */
        .brand-logo {
            position: absolute;
            right: 22px;
            top: 22px;
            height: 48px;
            opacity: 0.95;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,.4));
        }
        .watermark-logo {
            position: fixed;
            right: 24px;
            bottom: 24px;
            height: 44px;
            opacity: 0.12;
            pointer-events: none;
            user-select: none;
            z-index: 999;
        }
        @media (max-width: 640px) {
            .brand-logo { height: 32px; right: 12px; top: 12px; }
            .watermark-logo { height: 32px; right: 12px; bottom: 12px; }
        }
        
        .controls {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .control-group { display: flex; flex-direction: column; gap: 8px; }
        .control-group label { font-size: 0.9rem; color: #cbd5e1; }
        
        select, input, button {
            padding: 12px 16px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 14px;
        }
        
        button {
            background: linear-gradient(45deg, #8b5cf6, #06b6d4);
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover { transform: translateY(-5px); }
        
        .stat-card h3 {
            font-size: 0.9rem;
            color: #cbd5e1;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-value {
            font-size: 2.8rem;
            font-weight: bold;
            background: linear-gradient(45deg, #8b5cf6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            height: 400px;
        }
        
        .chart-title {
            font-size: 1.2rem;
            margin-bottom: 15px;
            text-align: center;
            color: #e2e8f0;
            font-weight: 600;
        }
        
        .loading, .error {
            text-align: center;
            padding: 40px;
            border-radius: 10px;
        }
        
        .loading { color: #cbd5e1; }
        .error { 
            color: #ef4444; 
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .refresh-info {
            text-align: center;
            padding: 10px;
            color: #94a3b8;
            font-size: 0.9rem;
        }
        
        .table-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-top: 20px;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        
        .data-table th, .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .data-table th {
            background: rgba(139, 92, 246, 0.3);
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .data-table tr:hover { background: rgba(255, 255, 255, 0.1); }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-completed { background: #22c55e; color: white; }
        .status-pending { background: #f59e0b; color: white; }
        .status-in-progress { background: #3b82f6; color: white; }
        .status-on-hold { background: #ef4444; color: white; }
        .status-blocked { background: #6b7280; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Department Analytics Dashboard</h1>
            <p>Real-time data visualization from Google Sheets</p>
            <img class="brand-logo" alt="COSMOS" src="{{ logo_src }}" />
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label>Data Source:</label>
                <select id="dataSource">
                    <option value="sheets">Google Sheets Direct</option>
                    <option value="backend">Apps Script Backend</option>
                </select>
            </div>
            <div class="control-group">
                <label>Google Sheets ID:</label>
                <input type="text" id="sheetId" placeholder="Your Google Sheets ID" style="width: 300px;">
            </div>
            <div class="control-group">
                <label>Department:</label>
                <select id="department">
                    <option value="Shell">Shell</option>
                    <option value="Modulation">Modulation</option>
                    <option value="MD">MD</option>
                    <option value="Area">Area</option>
                </select>
            </div>
            <!-- Person filter -->
            <div class="control-group">
                <label>Person:</label>
                <select id="personFilter">
                    <option value="">All</option>
                </select>
            </div>
            <div class="control-group">
                <label>&nbsp;</label>
                <button onclick="loadDashboard()">Load Dashboard</button>
            </div>
            <div class="control-group">
                <label>&nbsp;</label>
                <button onclick="toggleAutoRefresh()" id="refreshBtn">Auto Refresh: OFF</button>
            </div>
        </div>
        
        <div class="refresh-info">
            <span id="lastUpdated">Click 'Load Dashboard' to start</span>
        </div>
        
        <div id="dashboard-content">
            <div class="loading">
                <h3>Welcome to Your Analytics Dashboard</h3>
                <p>Configure your data source and click 'Load Dashboard' to begin</p>
            </div>
        </div>
    </div>

    <img class="watermark-logo" alt="COSMOS watermark" src="{{ logo_src }}" />

    <script>
        let refreshInterval = null;
        let autoRefreshEnabled = false;

        /* === NEW: Map department → ONLY-allowed person column === */
        const PERSON_KEY_MAP = {
          'Shell': 'Shell Plan By',
          'Modulation': 'Modulation Done By',
          'MD': 'MD Done By',
          'Area': 'Area Done By'
        };

        // case-insensitive key lookup in a row
        function findKeyCI(row, wanted){
          const w = wanted.toLowerCase();
          return Object.keys(row).find(k => k.toLowerCase() === w) || null;
        }

        // Build unique list of names from the department-specific column only
        function computePeople(data, department){
          const names = new Set();
          const wanted = PERSON_KEY_MAP[department];
          if (!wanted) return [];
          data.forEach(row => {
            const key = findKeyCI(row, wanted);
            const v = key ? (row[key] || '').toString().trim() : '';
            if (v) names.add(v);
          });
          return Array.from(names).sort((a,b)=>a.localeCompare(b));
        }
        function escapeHtml(str){
          return (str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
        }
        function populatePersonDropdown(data, department){
          const sel = document.getElementById('personFilter'); if (!sel) return;
          const prev = sel.value;
          const list = computePeople(data, department);
          sel.innerHTML = '<option value=\"\">All</option>' + list.map(n => '<option value=\"'+escapeHtml(n)+'\">'+escapeHtml(n)+'</option>').join('');
          if (list.includes(prev)) sel.value = prev;
        }
        
        async function loadDashboard() {
            const department = document.getElementById('department').value;
            const dataSource = document.getElementById('dataSource').value;
            const sheetId = document.getElementById('sheetId').value.trim();
            
            if (dataSource === 'sheets' && !sheetId) {
                alert('Please enter your Google Sheets ID');
                return;
            }
            
            showLoading();
            
            try {
                let data;
                if (dataSource === 'backend') {
                    // Fetch from Flask backend
                    const response = await fetch(`/api/data/${department}`);
                    data = await response.json();
                } else {
                    // Fetch directly from Google Sheets
                    data = await fetchFromSheets(sheetId, department);
                }

                // Rebuild People list using ONLY the department-specific column
                populatePersonDropdown(data, department);

                // Apply person filter using ONLY the department-specific column
                const personPick = (document.getElementById('personFilter')?.value || '').trim().toLowerCase();
                if (personPick) {
                    const wanted = PERSON_KEY_MAP[department];
                    data = data.filter(row => {
                        const key = wanted ? findKeyCI(row, wanted) : null;
                        const v = key ? (row[key] || '').toString().trim().toLowerCase() : '';
                        return v === personPick;
                    });
                }
                
                if (data && data.length > 0) {
                    renderDashboard(data, department);
                    updateTimestamp();
                } else {
                    showError('No data found. Check your Sheet ID and department tabs.');
                }
                
            } catch (error) {
                showError(`Error: ${error.message}`);
            }
        }
        
        async function fetchFromSheets(sheetId, department) {
            const url = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?tqx=out:csv&sheet=${department}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.status}`);
            }
            
            const csvText = await response.text();
            return parseCSV(csvText);
        }
        
        function parseCSV(csvText) {
            const lines = csvText.trim().split('\\n');
            if (lines.length < 2) return [];
            
            const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());
            const data = [];
            
            for (let i = 1; i < lines.length; i++) {
                const values = parseCSVLine(lines[i]);
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = values[index] || '';
                });
                data.push(row);
            }
            return data;
        }
        
        function parseCSVLine(line) {
            const values = [];
            let current = '';
            let inQuotes = false;
            
            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                if (char === '"') {
                    inQuotes = !inQuotes;
                } else if (char === ',' && !inQuotes) {
                    values.push(current.trim());
                    current = '';
                } else {
                    current += char;
                }
            }
            values.push(current.trim());
            return values;
        }
        
        function renderDashboard(data, department) {
            const stats = calculateKPIs(data, department);
            
            document.getElementById('dashboard-content').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Projects</h3>
                        <div class="stat-value">${stats.total}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Completed</h3>
                        <div class="stat-value">${stats.completed}</div>
                    </div>
                    <div class="stat-card">
                        <h3>In Progress</h3>
                        <div class="stat-value">${stats.inProgress}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Completion Rate</h3>
                        <div class="stat-value">${stats.completionRate}%</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total Area</h3>
                        <div class="stat-value">${stats.totalArea.toLocaleString()} sq m</div>
                    </div>
                </div>
                
                <div class="charts-grid">
                    <div class="chart-container">
                        <h3 class="chart-title">Status Distribution</h3>
                        <canvas id="statusChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3 class="chart-title">Work Type Analysis</h3>
                        <canvas id="workTypeChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3 class="chart-title">Monthly Progress</h3>
                        <canvas id="timelineChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3 class="chart-title">Area by Project</h3>
                        <canvas id="areaChart"></canvas>
                    </div>
                </div>
                
                <div class="table-container">
                    <h3 class="chart-title">Recent Records</h3>
                    <div style="overflow-x: auto;">
                        ${createDataTable(data)}
                    </div>
                </div>
            `;
            
            // Create charts
            setTimeout(() => {
                createStatusChart(data);
                createWorkTypeChart(data);
                createTimelineChart(data);
                createAreaChart(data, department);
            }, 100);
        }
        
        function calculateKPIs(data, department) {
            const total = data.length;
            const statusCounts = {};
            
            data.forEach(row => {
                const status = row.status || row['current status'] || 'Unknown';
                statusCounts[status] = (statusCounts[status] || 0) + 1;
            });
            
            const completed = statusCounts['Completed'] || statusCounts['completed'] || 0;
            const inProgress = statusCounts['In Progress'] || statusCounts['in progress'] || 0;
            
            // Calculate total area
            const areaField = department === 'Area' ? 'total area in sq meter' : 'area statement in sq meter';
            const totalArea = data.reduce((sum, row) => {
                const raw = row[areaField] || '';
                const num = parseFloat(raw.toString().replace(/,/g, '')); // tolerate commas
                return sum + (isNaN(num) ? 0 : num);
            }, 0);
            
            const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;
            
            return { total, completed, inProgress, completionRate, totalArea: Math.round(totalArea) };
        }
        
        function createStatusChart(data) {
            const statusCounts = {};
            data.forEach(row => {
                const status = row.status || row['current status'] || 'Unknown';
                const label = status.charAt(0).toUpperCase() + status.slice(1);
                statusCounts[label] = (statusCounts[label] || 0) + 1;
            });
            
            const ctx = document.getElementById('statusChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(statusCounts),
                    datasets: [{
                        data: Object.values(statusCounts),
                        backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#6b7280'],
                        borderWidth: 2,
                        borderColor: '#1f2937'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#e2e8f0' } }
                    }
                }
            });
        }
        
        function createWorkTypeChart(data) {
            const workTypes = {};
            data.forEach(row => {
                const work = row['kind of work (select from drop down)'] || row['kind of work'] || row['work type'] || 'Unknown';
                workTypes[work] = (workTypes[work] || 0) + 1;
            });
            
            const ctx = document.getElementById('workTypeChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(workTypes),
                    datasets: [{
                        label: 'Count',
                        data: Object.values(workTypes),
                        backgroundColor: 'rgba(6, 182, 212, 0.8)',
                        borderColor: '#06b6d4',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#e2e8f0' } } },
                    scales: {
                        x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                    }
                }
            });
        }
        
        function createTimelineChart(data) {
            const monthlyData = {};
            
            data.forEach(row => {
                const createdAt = row.created_at || row['created at'] || row['created'] || '';
                if (createdAt) {
                    const d = new Date(createdAt);
                    if (!isNaN(d.getTime())) {
                        const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
                        monthlyData[key] = (monthlyData[key] || 0) + 1;
                    }
                }
            });
            
            const months = Object.keys(monthlyData).sort();
            const counts = months.map(m => monthlyData[m]);
            
            const ctx = document.getElementById('timelineChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: [{
                        label: 'Projects',
                        data: counts,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.2)',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#e2e8f0' } } },
                    scales: {
                        x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                    }
                }
            });
        }
        
        function createAreaChart(data, department) {
            const areaField = department === 'Area' ? 'total area in sq meter' : 'area statement in sq meter';
            const areaData = data
                .filter(row => {
                    const num = parseFloat((row[areaField] || '').toString().replace(/,/g,''));
                    return !isNaN(num) && num > 0;
                })
                .slice(0, 12)
                .map(row => ({
                    project: row['Project Code'] || row['Project no'] || row['Project name'] || 'Unknown',
                    area: parseFloat((row[areaField] || '').toString().replace(/,/g,'')) || 0
                }));
            
            const ctx = document.getElementById('areaChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: areaData.map(d => d.project),
                    datasets: [{
                        label: 'Area (sq m)',
                        data: areaData.map(d => d.area),
                        backgroundColor: 'rgba(139, 92, 246, 0.8)',
                        borderColor: '#8b5cf6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { labels: { color: '#e2e8f0' } } },
                    scales: {
                        x: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                        y: { ticks: { color: '#cbd5e1' }, grid: { color: 'rgba(255,255,255,0.1)' } }
                    }
                }
            });
        }
        
        function createDataTable(data) {
            const displayCols = ['Project Code', 'status', 'expected date of finish'];
            const recentData = data.slice(0, 15);
            
            let html = '<table class="data-table"><thead><tr>';
            displayCols.forEach(col => html += `<th>${col}</th>`);
            html += '</tr></thead><tbody>';
            
            recentData.forEach(row => {
                html += '<tr>';
                displayCols.forEach(col => {
                    let value = row[col] || '';
                    if (col === 'status' && value) {
                        const statusClass = `status-${value.toLowerCase().replace(/\s+/g, '-')}`;
                        value = `<span class="status-badge ${statusClass}">${value}</span>`;
                    }
                    html += `<td>${value}</td>`;
                });
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            return html;
        }
        
        function showLoading() {
            document.getElementById('dashboard-content').innerHTML = 
                '<div class="loading"><h3>Loading...</h3><p>Fetching latest data...</p></div>';
        }
        
        function showError(msg) {
            document.getElementById('dashboard-content').innerHTML = 
                `<div class="error"><h3>Error</h3><p>${msg}</p></div>`;
        }
        
        function updateTimestamp() {
            document.getElementById('lastUpdated').textContent = 
                `Last updated: ${new Date().toLocaleString()}`;
        }
        
        function toggleAutoRefresh() {
            const btn = document.getElementById('refreshBtn');
            if (autoRefreshEnabled) {
                clearInterval(refreshInterval);
                autoRefreshEnabled = false;
                btn.textContent = 'Auto Refresh: OFF';
            } else {
                refreshInterval = setInterval(loadDashboard, 30000);
                autoRefreshEnabled = true;
                btn.textContent = 'Auto Refresh: ON';
            }
        }

        // Reload when person selection changes
        document.addEventListener('DOMContentLoaded', () => {
            const pf = document.getElementById('personFilter');
            if (pf) pf.addEventListener('change', loadDashboard);
        });
    </script>
</body>
</html>
    """
    return render_template_string(html_template, logo_src=logo_src)

@app.route('/api/data/<department>')
def get_data(department):
    """API endpoint to get department data"""
    df = fetch_data_from_backend(department)
    return jsonify(df.to_dict('records'))

if __name__ == '__main__':
    print("Starting Dashboard Server...")
    print("Dashboard will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, host='0.0.0.0', port=5000)
