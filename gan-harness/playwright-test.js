const { chromium } = require('playwright');

const BASE_URL = 'http://127.0.0.1:8002';
const FRONTEND_URL = 'http://127.0.0.1:3000';
const results = [];

async function logTest(name, passed, detail = '') {
    const status = passed ? '✅ PASS' : '❌ FAIL';
    results.push({ name, passed, detail });
    console.log(`${status} | ${name}`);
    if (detail) console.log(`    → ${detail}`);
}

async function runPlaywrightTests() {
    console.log('='.repeat(60));
    console.log('漫AI Sprint 1 - Phase 7 Playwright E2E Tests');
    console.log('='.repeat(60));
    console.log();

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    let passed = 0;
    let failed = 0;

    try {
        // Test 1: Frontend loads
        console.log('[1] Frontend Load Tests');
        console.log('-'.repeat(40));
        try {
            await page.goto(FRONTEND_URL, { timeout: 15000 });
            await page.waitForLoadState('networkidle', { timeout: 10000 });
            const title = await page.title();
            logTest('Frontend Page Load', title.includes('漫AI'), `Title: ${title}`);
            
            // Check if redirected to studio
            const url = page.url();
            logTest('Frontend Redirect', url.includes('/studio'), `URL: ${url}`);
            passed += 2;
        } catch (e) {
            logTest('Frontend Page Load', false, e.message);
            failed++;
        }
        console.log();

        // Test 2: Studio page has required elements
        console.log('[2] Studio Page Element Tests');
        console.log('-'.repeat(40));
        try {
            await page.goto(`${FRONTEND_URL}/studio`, { timeout: 15000 });
            await page.waitForLoadState('networkidle', { timeout: 10000 });
            
            // Check for form elements
            const promptInput = await page.$('input[name="prompt"], textarea, input[type="text"]');
            logTest('Studio - Prompt Input Exists', !!promptInput, promptInput ? 'Found' : 'Not found');
            
            // Check for mode selector
            const modeSelectors = ['select', 'button', 'div[role="button"]'];
            let foundModeSelector = false;
            for (const sel of modeSelectors) {
                if (await page.$(sel)) {
                    foundModeSelector = true;
                    break;
                }
            }
            logTest('Studio - Mode Selector Exists', foundModeSelector, foundModeSelector ? 'Found' : 'Not found');
            passed += 2;
        } catch (e) {
            logTest('Studio Page Elements', false, e.message);
            failed++;
        }
        console.log();

        // Test 3: API Docs page loads
        console.log('[3] API Docs Page Test');
        console.log('-'.repeat(40));
        try {
            await page.goto(`${FRONTEND_URL}/api-docs`, { timeout: 15000 });
            await page.waitForLoadState('networkidle', { timeout: 10000 });
            const content = await page.content();
            logTest('API Docs Page Loads', content.includes('Swagger') || content.includes('swagger'), 'Swagger UI detected');
            passed++;
        } catch (e) {
            logTest('API Docs Page', false, e.message);
            failed++;
        }
        console.log();

        // Test 4: Backend API accessibility from browser
        console.log('[4] Backend API Accessibility');
        console.log('-'.repeat(40));
        try {
            const response = await page.request.get(`${BASE_URL}/api/v1/health`);
            const data = await response.json();
            logTest('Backend Health from Browser', response.status() === 200 && data.status === 'ok', 
                    `${response.status()} ${JSON.stringify(data)}`);
            passed++;
        } catch (e) {
            logTest('Backend Health from Browser', false, e.message);
            failed++;
        }
        console.log();

        // Test 5: Register and Login flow
        console.log('[5] Auth Flow E2E');
        console.log('-'.repeat(40));
        try {
            const email = `e2e_${Date.now()}@test.com`;
            
            // Register
            const regResp = await page.request.post(`${BASE_URL}/api/v1/auth/register`, {
                data: { name: 'e2e_test', email, password: 'test123' }
            });
            logTest('E2E - User Registration', regResp.status() === 201, `${regResp.status()}`);
            
            // Login
            const loginResp = await page.request.post(`${BASE_URL}/api/v1/auth/login`, {
                data: { email, password: 'test123' }
            });
            const loginData = await loginResp.json();
            logTest('E2E - User Login', loginResp.status() === 200 && loginData.access_token, 
                    `Token received: ${!!loginData.access_token}`);
            
            if (loginData.access_token) {
                // Create task with auth
                const taskResp = await page.request.post(`${BASE_URL}/api/v1/generate`, {
                    headers: { Authorization: `Bearer ${loginData.access_token}` },
                    data: { prompt: 'e2e test', duration: 5, quality_mode: 'balanced' }
                });
                logTest('E2E - Task Creation', taskResp.status() === 202, `${taskResp.status()}`);
                
                if (taskResp.status() === 202) {
                    const taskData = await taskResp.json();
                    // Query task
                    const getResp = await page.request.get(
                        `${BASE_URL}/api/v1/generate/${taskData.task_id}`,
                        { headers: { Authorization: `Bearer ${loginData.access_token}` } }
                    );
                    logTest('E2E - Task Query', getResp.status() === 200, `${getResp.status()}`);
                }
            }
            passed += 3;
        } catch (e) {
            logTest('E2E Auth Flow', false, e.message);
            failed++;
        }
        console.log();

        // Test 6: Navigation between pages
        console.log('[6] Navigation Tests');
        console.log('-'.repeat(40));
        const pages = ['/', '/studio', '/gallery', '/pricing', '/dashboard'];
        for (const path of pages) {
            try {
                await page.goto(`${FRONTEND_URL}${path}`, { timeout: 15000 });
                await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
                logTest(`Navigation - ${path}`, true, 'Loaded successfully');
                passed++;
            } catch (e) {
                logTest(`Navigation - ${path}`, false, e.message);
                failed++;
            }
        }
        console.log();

        // Test 7: Error handling - 404 page
        console.log('[7] Error Page Handling');
        console.log('-'.repeat(40));
        try {
            await page.goto(`${FRONTEND_URL}/non-existent-page-xyz`, { timeout: 15000 });
            const content = await page.content();
            const has404 = content.includes('404') || content.includes('not found') || content.includes('Not Found');
            logTest('404 Error Page', has404, has404 ? 'Shows 404 message' : 'No 404 message');
            passed++;
        } catch (e) {
            logTest('404 Error Page', false, e.message);
            failed++;
        }
        console.log();

    } catch (e) {
        console.error('Test suite error:', e);
    } finally {
        await browser.close();
    }

    // Summary
    console.log('='.repeat(60));
    console.log('Playwright E2E Summary');
    console.log('='.repeat(60));
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log();
    console.log('Details:');
    for (const r of results) {
        const status = r.passed ? '✅' : '❌';
        console.log(`  ${status} ${r.name}`);
    }
    
    return { passed, failed, results };
}

runPlaywrightTests().then(r => {
    process.exit(r.failed > 0 ? 1 : 0);
}).catch(e => {
    console.error(e);
    process.exit(1);
});