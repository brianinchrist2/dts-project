const apiClient = {
  get: async (url) => {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return { data: await response.json() };
  }
};

async function test() {
  try {
    console.log("Testing /api/system/health...");
    const health = await apiClient.get('http://152.32.201.243/api/system/health');
    console.log("Health:", health);

    console.log("Testing /api/account/info...");
    const account = await apiClient.get('http://152.32.201.243/api/account/info');
    console.log("Account:", account);
  } catch (e) {
    console.error("Error:", e);
  }
}

test();
