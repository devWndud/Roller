// auth.js - client-side helpers for Google (Firebase) and Kakao sign-in

// -- Google (Firebase) --
// NOTE: user must add their Firebase web config in firebaseConfig below.
// Example:
// const firebaseConfig = {
//   apiKey: "...",
//   authDomain: "...",
//   projectId: "...",
//   appId: "...",
// };

let firebaseApp;
function initFirebase(firebaseConfig) {
    if (!firebaseConfig) return console.warn('Firebase config not provided');
    if (!window.firebase || !window.firebase.auth) return console.warn('Firebase SDK not loaded');
    firebaseApp = firebase.initializeApp(firebaseConfig);
}

async function googleSignIn() {
    if (!window.firebase || !window.firebase.auth) {
        alert('Firebase SDK not loaded.');
        return;
    }
    const provider = new firebase.auth.GoogleAuthProvider();
    try {
        const result = await firebase.auth().signInWithPopup(provider);
        // Signed in
        const user = result.user;
        console.log('Google sign-in success', user);
        // send ID token to server to establish session
        const idToken = await user.getIdToken();
        const resp = await fetch('/sessionLogin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken })
        });
        const json = await resp.json().catch(() => ({}));
        if (!resp.ok) {
            console.error('sessionLogin error', json);
            alert('서버 세션 생성 실패: ' + (json.error || resp.status));
            return;
        }
        // redirect to home (not reload) to show updated server-rendered nav
        window.location = '/';
    } catch (err) {
        console.error(err);
        alert('Google sign-in failed: ' + err.message);
    }
}

// -- Kakao --
// Requires Kakao JS SDK to be loaded via <script src="https://developers.kakao.com/sdk/js/kakao.js"></script>
// and Kakao.init('<YOUR_JS_KEY>') called before using kakaoSignIn.

function kakaoSignIn() {
    if (!window.Kakao) {
        alert('Kakao SDK not loaded.');
        return;
    }

    Kakao.Auth.login({
        success: function(authObj) {
            const accessToken = authObj.access_token;
            // Send to backend to mint Firebase custom token
            fetch('/auth/kakao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ access_token: accessToken })
            })
            .then(r => r.json())
            .then(async data => {
                if (data.customToken) {
                    if (!window.firebase || !window.firebase.auth) {
                        alert('Firebase SDK not loaded; cannot sign in with custom token.');
                        return;
                    }
                    try {
                        const res = await firebase.auth().signInWithCustomToken(data.customToken);
                        const user = res.user;
                        // send ID token to server to establish session
                        const idToken = await user.getIdToken();
                        await fetch('/sessionLogin', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ idToken })
                        });
                        const resp2 = await fetch('/sessionLogin', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ idToken }) });
                        const json2 = await resp2.json().catch(() => ({}));
                        if (!resp2.ok) {
                            console.error('sessionLogin error', json2);
                            alert('서버 세션 생성 실패: ' + (json2.error || resp2.status));
                            return;
                        }
                        window.location = '/';
                    } catch (err) {
                        console.error('Sign in with custom token failed', err);
                        alert('Firebase custom token sign-in failed: ' + err.message);
                    }
                } else {
                    console.error('No customToken from server', data);
                    alert('서버에서 인증 토큰을 받지 못했습니다. 콘솔 확인');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Kakao auth exchange failed');
            });
        },
        fail: function(err) {
            console.error(err);
            alert('Kakao login failed');
        }
    });
}

// Toggle header UI based on Firebase auth state
function applyAuthUi(user) {
    const guest = document.getElementById('auth-guest');
    const usr = document.getElementById('auth-user');
    if (!guest || !usr) return;
    if (user) {
        guest.style.display = 'none';
        usr.style.display = 'flex';  // show as flex to align with header-right layout
    } else {
        guest.style.display = 'flex';
        usr.style.display = 'none';
    }
}

function attachLogoutHandler() {
    const link = document.getElementById('logout-link');
    if (!link) return;
    link.addEventListener('click', async function(e) {
        e.preventDefault();
        try {
            if (window.firebase && window.firebase.auth) {
                await firebase.auth().signOut();
            }
        } catch (err) {
            console.warn('Firebase signOut failed', err);
        }
        // call server logout to clear session
        try {
            await fetch('/logout');
        } catch (err) {
            console.warn('Server logout failed', err);
        }
        window.location.reload();
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const headerAuth = document.getElementById('header-auth');
    const guest = document.getElementById('auth-guest');
    const user = document.getElementById('auth-user');
    
    // Initialize UI based on server-rendered state (to prevent flash)
    const isLoggedIn = headerAuth && headerAuth.getAttribute('data-logged-in') === 'true';
    if (guest && user) {
        if (isLoggedIn) {
            guest.style.display = 'none';
            user.style.display = 'flex';
        } else {
            guest.style.display = 'flex';
            user.style.display = 'none';
        }
    }
    
    attachLogoutHandler();
    if (window.firebase && window.firebase.auth) {
        // set up auth state listener for UI updates
        firebase.auth().onAuthStateChanged(function(user) {
            applyAuthUi(user);
            // if user is authed in Firebase, sync to server if needed
            if (user) {
                syncAuthToServer(user);
            }
        });
    }
});

// Sync Firebase auth to server session if server session missing
async function syncAuthToServer(user) {
    if (!user) return;
    try {
        const resp = await fetch('/api/auth/status');
        const status = await resp.json();
        if (!status.loggedIn) {
            // server session missing; create it
            const idToken = await user.getIdToken();
            const syncResp = await fetch('/sessionLogin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ idToken })
            });
            const syncJson = await syncResp.json().catch(() => ({}));
            if (!syncResp.ok) {
                console.warn('Failed to sync auth to server:', syncJson.error);
            } else {
                console.log('Auth synced to server');
                applyAuthUi(user);
            }
        }
    } catch (err) {
        console.error('Error syncing auth to server:', err);
    }
}
