export const Theme = {
    colors: {
        background: '#080808',
        primary: '#FFFFFF',
        secondary: '#555555',
        positive: '#22C55E',
        warning: '#F59E0B',
        critical: '#EF4444',
        border: '#1A1A1A',
        black: '#000000',
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
