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
            }
        };
        // Check every 2 seconds for token changes (simpler than complex event emitters for now)
        const interval = setInterval(checkToken, 2000);
        checkToken();
        return () => clearInterval(interval);
    }, [token]);

    const connect = () => {
        if (!token) {
            console.log('Socket: No token available, skipping connection.');
            return;
        }
        if (socket && socket.readyState <= 1) {
            console.log('Socket: already connected or connecting.');
            return;
        }

        console.log('Attempting Patient WS Connection...');

        try {
            const ws = new WebSocket(`${WS_BASE_URL}/ws/${token}`);

            ws.onopen = () => {
                console.log('Patient WebSocket Connected');
                setSocket(ws);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Patient WS Message:', data);
                    if (data.type === 'consent_request') {
                        // Global alert for consent requests
                        Alert.alert("New Access Request", data.message);
                    }
                    setLastMessage(data);
                } catch (e) {
                    console.error('Patient WS Parse Error:', e);
                }
            };

            ws.onclose = () => {
                console.log('Patient WebSocket Disconnected. Retrying in 5s...');
                setSocket(null);
                if (token) {
                    reconnectTimer.current = setTimeout(connect, 5000);
                }
            };

            ws.onerror = (err) => {
                console.error('Patient WebSocket Error:', err);
                // On error, let onclose handle reconnection
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
