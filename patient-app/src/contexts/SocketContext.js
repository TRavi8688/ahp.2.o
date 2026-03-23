import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import { WS_BASE_URL } from '../api';

const SocketContext = createContext();

export const useSocket = () => useContext(SocketContext);

export const SocketProvider = ({ children }) => {
    const [socket, setSocket] = useState(null);
    const [lastMessage, setLastMessage] = useState(null);
    const [token, setToken] = useState(null);
    const reconnectTimer = useRef(null);

    // Watch for token in AsyncStorage
    useEffect(() => {
        const checkToken = async () => {
            const storedToken = await AsyncStorage.getItem('token');
            if (storedToken !== token) {
                console.log('Token changed or detected:', storedToken ? 'Token Present' : 'No Token');
                setToken(storedToken);
                setRetryCount(0); // Reset retries when we get a fresh token string
            }
        };
        // Check every 2 seconds for token changes (simpler than complex event emitters for now)
        const interval = setInterval(checkToken, 2000);
        checkToken();
        return () => clearInterval(interval);
    }, [token]);

    const [retryCount, setRetryCount] = useState(0);
    const MAX_RETRIES = 5;

    const connect = async () => {
        // 1. Fetch the MOST RECENT token directly from storage
        const latestToken = await AsyncStorage.getItem('token');
        
        if (!latestToken) {
            console.log('Socket: No token in storage, skipping connection.');
            return;
        }

        if (socket && socket.readyState <= 1) {
            console.log('Socket: already connected or connecting.');
            return;
        }

        if (retryCount >= MAX_RETRIES) {
            console.warn('Socket: Max retries reached with current token. Please re-login.');
            return;
        }

        console.log(`Attempting Patient WS Connection (Attempt ${retryCount + 1})...`);

        try {
            const ws = new WebSocket(`${WS_BASE_URL}/ws/${latestToken}`);

            ws.onopen = () => {
                console.log('Patient WebSocket Connected');
                setSocket(ws);
                setRetryCount(0); // Reset on success
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Patient WS Message:', data);
                    if (data.type === 'consent_request') {
                        Alert.alert("New Access Request", data.message);
                    }
                    setLastMessage(data);
                } catch (e) {
                    console.error('Patient WS Parse Error:', e);
                }
            };

            ws.onclose = (e) => {
                console.log(`Patient WebSocket Closed. Status: ${e.code}. Retrying...`);
                setSocket(null);
                
                // If it's a policy violation (likely expired token), don't retry immediately
                const delay = e.code === 1008 ? 30000 : 5000; 
                
                if (latestToken) {
                    setRetryCount(prev => prev + 1);
                    reconnectTimer.current = setTimeout(connect, delay);
                }
            };

            ws.onerror = (err) => {
                console.error('Patient WebSocket Error:', err);
            };
        } catch (err) {
            console.error('WebSocket Initialization Error:', err);
        }
    };

    useEffect(() => {
        if (token) {
            connect();
        } else {
            console.log('Token removed, closing socket.');
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
