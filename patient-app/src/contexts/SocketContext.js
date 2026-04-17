import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import { WS_BASE_URL } from '../api';

const SocketContext = createContext();

export const useSocket = () => useContext(SocketContext);

// Must match the key used in SecurityUtils
const TOKEN_KEY = 'mulajna_auth_token';

export const SocketProvider = ({ children }) => {
    const [socket, setSocket] = useState(null);
    const [lastMessage, setLastMessage] = useState(null);
    const [token, setToken] = useState(null);
    const [retryCount, setRetryCount] = useState(0);
    const reconnectTimer = useRef(null);
    const MAX_RETRIES = 5;

    // Watch for token changes in AsyncStorage using the correct key
    useEffect(() => {
        const checkToken = async () => {
            const storedToken = await AsyncStorage.getItem(TOKEN_KEY);
            if (storedToken !== token) {
                console.log('[Socket] Token changed:', storedToken ? 'Present' : 'Cleared');
                setToken(storedToken);
                setRetryCount(0); // Reset retries when token changes
            }
        };
        const interval = setInterval(checkToken, 2000);
        checkToken();
        return () => clearInterval(interval);
    }, [token]);

    const connect = async () => {
        const latestToken = await AsyncStorage.getItem(TOKEN_KEY);

        if (!latestToken) {
            console.log('[Socket] No token found, skipping connection.');
            return;
        }

        if (socket && socket.readyState <= 1) {
            console.log('[Socket] Already connected or connecting.');
            return;
        }

        if (retryCount >= MAX_RETRIES) {
            console.warn('[Socket] Max retries reached. Please re-login.');
            return;
        }

        console.log(`[Socket] Connecting... (Attempt ${retryCount + 1})`);

        try {
            const ws = new WebSocket(`${WS_BASE_URL}/ws/${latestToken}`);

            ws.onopen = () => {
                console.log('[Socket] Patient WebSocket Connected ✅');
                setSocket(ws);
                setRetryCount(0);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[Socket] Message received:', data.type);
                    if (data.type === 'consent_request') {
                        Alert.alert('New Access Request', data.message);
                    }
                    setLastMessage(data);
                } catch (e) {
                    console.error('[Socket] Parse Error:', e);
                }
            };

            ws.onclose = (e) => {
                console.log(`[Socket] Closed. Code: ${e.code}`);
                setSocket(null);
                const delay = e.code === 1008 ? 30000 : 5000;
                if (latestToken) {
                    setRetryCount(prev => prev + 1);
                    reconnectTimer.current = setTimeout(connect, delay);
                }
            };

            ws.onerror = (err) => {
                console.error('[Socket] Error:', err.message || err);
            };
        } catch (err) {
            console.error('[Socket] Initialization Error:', err);
        }
    };

    useEffect(() => {
        if (token) {
            connect();
        } else {
            console.log('[Socket] No token — closing socket.');
            if (socket) {
                socket.close();
                setSocket(null);
            }
        }
        return () => {
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        };
    }, [token]);

    return (
        <SocketContext.Provider value={{ socket, lastMessage }}>
            {children}
        </SocketContext.Provider>
    );
};
