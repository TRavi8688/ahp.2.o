import React, { useState, useEffect, useRef } from 'react';
import {
    View, Text, StyleSheet, FlatList, TextInput,
    TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform, Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Theme, GlobalStyles } from '../theme';
import { API_BASE_URL } from '../api';

const { width } = Dimensions.get('window');

export default function ChittiAiScreen({ navigation }) {
    const [messages, setMessages] = useState([
        { id: '1', sender: 'ai', text: 'Namaste! I am Chitti, your AHP Clinical Guardian. I have synchronized your medical records and I am ready to assist. What can we discuss today?' }
    ]);
    const [inputText, setInputText] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const flatListRef = useRef();

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const token = await AsyncStorage.getItem('token');
                const resp = await axios.get(`${API_BASE_URL}/patient/chat-history`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                if (resp.data.length > 0) {
                    const formatted = resp.data.map((m, i) => ({
                        id: i.toString(),
                        sender: m.sender,
                        text: m.message_text
                    }));
                    setMessages(formatted);
                }
            } catch (e) {
                console.log("History fetch failed", e);
            }
        };
        fetchHistory();
    }, []);

    const sendMessage = async () => {
        if (!inputText.trim()) return;

        const userMsg = { id: Date.now().toString(), sender: 'user', text: inputText };
        setMessages(prev => [...prev, userMsg]);
        const textToSend = inputText;
        setInputText('');
        setIsTyping(true);

        try {
            const token = await AsyncStorage.getItem('token');
            const formData = new FormData();
            formData.append('text', textToSend);
            formData.append('language_code', 'en-IN');

            const response = await axios.post(`${API_BASE_URL}/patient/chat`, formData, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const aiMsg = { id: (Date.now() + 1).toString(), sender: 'ai', text: response.data.ai_text };
            setMessages(prev => [...prev, aiMsg]);

        } catch (error) {
            console.error('Chat error:', error);
            const errorMsg = { id: (Date.now() + 1).toString(), sender: 'ai', text: 'Error connecting to the brain.' };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsTyping(false);
        }
    };

    const renderItem = ({ item }) => {
        const isAI = item.sender === 'ai' || item.sender === 'chitti';
        return (
            <View style={[styles.messageBlock, isAI ? styles.aiBlock : styles.userBlock]}>
                <Text style={[styles.messageText, isAI ? styles.aiText : styles.userText]}>
                    {item.text}
                </Text>
            </View>
        );
    };

    return (
        <View style={GlobalStyles.screen}>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : null}
                style={{ flex: 1 }}
                keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
            >
                {/* Header */}
                <View style={styles.header}>
                    <TouchableOpacity onPress={() => navigation?.goBack()} style={styles.backBtn}>
                        <Ionicons name="arrow-back" size={24} color="#fff" />
                    </TouchableOpacity>
                    <View style={styles.headerInfo}>
                        <Text style={styles.headerTitle}>CHITTI AI</Text>
                        <Text style={styles.headerStatus}>SYNAPSE ACTIVE</Text>
                    </View>
                </View>

                <FlatList
                    ref={flatListRef}
                    data={messages}
                    renderItem={renderItem}
                    keyExtractor={item => item.id}
                    contentContainerStyle={styles.listContent}
                    onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
                    showsVerticalScrollIndicator={false}
                    inverted={false}
                />

                {isTyping && (
                    <View style={styles.typingIndicator}>
                        <Text style={styles.typingText}>SYNTHESIZING...</Text>
                    </View>
                )}

                {/* Input Area */}
                <View style={styles.inputArea}>
                    <View style={styles.inputWrapper}>
                        <TextInput
                            style={styles.input}
                            placeholder="TYPE A HEALTH QUERY..."
                            placeholderTextColor="#555"
                            value={inputText}
                            onChangeText={setInputText}
                            multiline
                        />
                        <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
                            <Ionicons name="arrow-up" size={24} color="#000" />
                        </TouchableOpacity>
                    </View>
                </View>
            </KeyboardAvoidingView>
        </View>
    );
}

const styles = StyleSheet.create({
    header: {
        paddingTop: 60,
        paddingHorizontal: 20,
        paddingBottom: 20,
        flexDirection: 'row',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#1A1A1A',
    },
    backBtn: {
        marginRight: 20,
    },
    headerInfo: {
        flex: 1,
    },
    headerTitle: {
        fontFamily: Theme.fonts.headingSemi,
        color: Theme.colors.primary,
        fontSize: 18,
        letterSpacing: 2,
    },
    headerStatus: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 9,
        marginTop: 2,
    },
    listContent: {
        padding: 20,
        paddingBottom: 120,
    },
    messageBlock: {
        maxWidth: '85%',
        padding: 20,
        marginBottom: 20,
        borderWidth: 1,
    },
    aiBlock: {
        alignSelf: 'flex-start',
        backgroundColor: '#000000',
        borderColor: '#FFFFFF',
    },
    userBlock: {
        alignSelf: 'flex-end',
        backgroundColor: '#FFFFFF',
        borderColor: '#FFFFFF',
    },
    messageText: {
        fontFamily: Theme.fonts.body,
        fontSize: 14,
        lineHeight: 22,
    },
    aiText: {
        color: '#FFFFFF',
    },
    userText: {
        color: '#000000',
    },
    typingIndicator: {
        paddingHorizontal: 20,
        paddingBottom: 10,
    },
    typingText: {
        fontFamily: Theme.fonts.label,
        color: Theme.colors.secondary,
        fontSize: 9,
        letterSpacing: 2,
    },
    inputArea: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        padding: 20,
        backgroundColor: '#080808',
    },
    inputWrapper: {
        flexDirection: 'row',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#FFFFFF',
        backgroundColor: '#000000',
        minHeight: 60,
        paddingHorizontal: 15,
    },
    input: {
        flex: 1,
        color: '#FFFFFF',
        fontFamily: Theme.fonts.body,
        fontSize: 14,
        maxHeight: 100,
        paddingVertical: 10,
    },
    sendButton: {
        backgroundColor: '#FFFFFF',
        width: 40,
        height: 40,
        justifyContent: 'center',
        alignItems: 'center',
        marginLeft: 10,
    }
});
