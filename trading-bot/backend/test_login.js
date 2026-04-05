const axios = require("axios");

async function testLogin() {
  try {
    const params = new URLSearchParams();
    params.append("username", "Khalil@gmail.com");
    params.append("password", "your_password_here"); // Assuming you have a way to know or test a known user

    // Let's try with test@example.com which I saw in the DB
    const params2 = new URLSearchParams();
    params2.append("username", "test@example.com");
    params2.append("password", "testpassword"); // Assuming default or common test pass

    const res = await axios.post("http://localhost:8000/token", params2, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    console.log("Login Status:", res.status);
    console.log("Token Received:", !!res.data.access_token);
  } catch (err) {
    console.error("Login Failed:", err.response?.data || err.message);
  }
}

testLogin();
