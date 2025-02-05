const axios = require('axios');

async function searchGoogle(query) {
    const API_KEY = process.env.GOOGLE_API_KEY;
    const CX = process.env.GOOGLE_CX;
    
    if (!API_KEY || !CX) {
        throw new Error('Missing required environment variables: GOOGLE_API_KEY and/or GOOGLE_CX');
    }
    
    const url = `https://www.googleapis.com/customsearch/v1?q=${encodeURIComponent(query)}&key=${API_KEY}&cx=${CX}`;
    
    try {
        const response = await axios.get(url);
        return JSON.stringify(response.data);
    } catch (error) {
        return JSON.stringify({ error: error.message });
    }
}

// Handle input from Python
const query = process.argv[2];
if (query) {
    searchGoogle(query)
        .then(result => {
            console.log(result);
            process.exit(0);
        })
        .catch(error => {
            console.error(JSON.stringify({ error: error.message }));
            process.exit(1);
        });
} 