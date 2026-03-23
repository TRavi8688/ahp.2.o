export const Theme = {
    colors: {
        background: '#050810',
        primary: '#6366F1', // Premium Indigo
        secondary: '#94A3B8', // Slate
        positive: '#22C55E',
        warning: '#F59E0B',
        critical: '#EF4444',
        border: '#1E293B',
        black: '#000000',
        white: '#FFFFFF',
    },
    fonts: {
        heading: 'Syne_800ExtraBold',
        headingSemi: 'Syne_700Bold',
        label: 'SpaceMono_400Regular',
        body: 'DMSans_400Regular',
    }
};

export const GlobalStyles = {
    screen: {
        flex: 1,
        backgroundColor: '#080808',
    },
    heading: {
        fontFamily: Theme.fonts.heading,
        color: '#FFFFFF',
    },
    label: {
        fontFamily: Theme.fonts.label,
        color: '#555555',
        textTransform: 'uppercase',
        letterSpacing: 1,
    },
    body: {
        fontFamily: Theme.fonts.body,
        color: '#FFFFFF',
    },
    sharpBorder: {
        borderWidth: 1,
        borderColor: '#FFFFFF',
        borderRadius: 0,
    }
};
