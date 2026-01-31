import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for Browser-native Text-to-Speech
 * Ensures safety on unmount and navigation.
 */
export const useTextToSpeech = () => {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isSupported, setIsSupported] = useState(false);
    const utteranceRef = useRef(null);

    useEffect(() => {
        if (typeof window !== 'undefined' && window.speechSynthesis) {
            setIsSupported(true);
        }
    }, []);

    const stop = useCallback(() => {
        if (!isSupported) return;
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
    }, [isSupported]);

    const speak = useCallback((text) => {
        if (!isSupported || !text) return;

        // Stop any current speech
        stop();

        // Create new utterance
        const utterance = new SpeechSynthesisUtterance(text);

        // Select a better voice if available (preference for Google US or natural voices)
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.lang === 'en-US' && v.name.includes('Google')) || voices.find(v => v.lang === 'en-US');
        if (preferredVoice) utterance.voice = preferredVoice;

        utteranceRef.current = utterance;

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = (e) => {
            console.error("TTS Error:", e);
            setIsSpeaking(false);
        };

        // Optional: Select a better voice if available
        // const voices = window.speechSynthesis.getVoices();
        // utterance.voice = voices.find(v => v.lang === 'en-US') || null;

        window.speechSynthesis.speak(utterance);
    }, [isSupported, stop]);

    // Cleanup on unmount to prevent background talking
    useEffect(() => {
        return () => {
            stop();
        };
    }, [stop]);

    return { isSpeaking, speak, stop, isSupported };
};
