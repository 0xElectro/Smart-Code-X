import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppTheme {
  // Light Mode Color Palette
  static const Color lightPrimaryColor =
      Color(0xFF5A4FCF); // Deeper slate blue - better contrast on light
  static const Color lightSecondaryColor =
      Color(0xFF00B8D4); // Deeper cyan - better visibility
  static const Color lightAccentColor = Color(0xFFE53935); // Red accent color
  static const Color lightBackgroundColor =
      Color(0xFFFEFBFF); // Soft light base
  static const Color lightSurfaceColor =
      Color(0xFFFEFBFF); // Pure white - elevated surfaces
  static const Color lightCardColor =
      Color(0xFFE3E1EC); // Light grey-blue - subtle cards

  // Dark Mode Color Palette
  static const Color darkPrimaryColor =
      Color(0xFF7B68EE); // Slate blue - vibrant
  static const Color darkSecondaryColor = Color(0xFF00E5FF); // Bright cyan
  static const Color darkAccentColor = Color(0xFFFF6B6B); // Coral red
  static const Color darkBackgroundColor = Color(0xFF0D1117); // Near black
  static const Color darkSurfaceColor = Color(0xFF161B22); // Dark grey-blue
  static const Color darkCardColor = Color(0xFF21262D); // Medium grey

  // Helper method to get colors based on brightness
  static Color getPrimaryColor(bool isDark) =>
      isDark ? darkPrimaryColor : lightPrimaryColor;
  static Color getSecondaryColor(bool isDark) =>
      isDark ? darkSecondaryColor : lightSecondaryColor;
  static Color getAccentColor(bool isDark) =>
      isDark ? darkAccentColor : lightAccentColor;
  static Color getBackgroundColor(bool isDark) =>
      isDark ? darkBackgroundColor : lightBackgroundColor;
  static Color getSurfaceColor(bool isDark) =>
      isDark ? darkSurfaceColor : lightSurfaceColor;
  static Color getCardColor(bool isDark) =>
      isDark ? darkCardColor : lightCardColor;

  static const ColorScheme lightColorScheme = ColorScheme(
    brightness: Brightness.light,
    primary: Color(0xFF5A4FCF),
    onPrimary: Colors.white,
    secondary: Color(0xFF00B8D4),
    onSecondary: Colors.white,
    tertiary: Color(0xFFE53935),
    onTertiary: Colors.white,
    error: Color(0xFFBA1A1A),
    onError: Colors.white,
    errorContainer: Color(0xFFFFDAD6),
    onErrorContainer: Color(0xFF410002),
    background: Color(0xFFFEFBFF),
    onBackground: Color(0xFF1A1C1E),
    surface: Color(0xFFFEFBFF),
    onSurface: Color(0xFF1A1C1E),
    surfaceVariant: Color(0xFFE3E1EC),
    onSurfaceVariant: Color(0xFF46464F),
    outline: Color(0xFF767680),
    outlineVariant: Color(0xFFC7C5D0),
    shadow: Colors.black,
    scrim: Colors.black,
    inverseSurface: Color(0xFF2F3033),
    onInverseSurface: Color(0xFFF1F0F4),
    inversePrimary: Color(0xFFB1B2FF),
    surfaceTint: Color(0xFF5A4FCF),
  );

  static const ColorScheme darkColorScheme = ColorScheme(
    brightness: Brightness.dark,
    primary: Color(0xFF7B68EE),
    onPrimary: Colors.white,
    secondary: Color(0xFF00E5FF),
    onSecondary: Color(0xFF000000),
    tertiary: Color(0xFFFF6B6B),
    onTertiary: Colors.white,
    error: Color(0xFFFF6B6B),
    onError: Colors.white,
    errorContainer: Color(0xFFFF5252),
    onErrorContainer: Colors.white,
    background: Color(0xFF0D1117),
    onBackground: Color(0xFFE0E0E0),
    surface: Color(0xFF161B22),
    onSurface: Color(0xFFE0E0E0),
    surfaceVariant: Color(0xFF21262D),
    onSurfaceVariant: Color(0xFFB0B0B0),
    outline: Color(0xFF595959),
    outlineVariant: Color(0xFF3A3A3A),
    shadow: Colors.black,
    scrim: Colors.black,
    inverseSurface: Color(0xFFE0E0E0),
    onInverseSurface: Color(0xFF1A1A1A),
    inversePrimary: Color(0xFF5A4FCF),
    surfaceTint: Color(0xFF7B68EE),
  );

  static LinearGradient getPrimaryGradient(bool isDark) => LinearGradient(
        colors: [getPrimaryColor(isDark), getSecondaryColor(isDark)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      );

  static LinearGradient getAccentGradient(bool isDark) => LinearGradient(
        colors: [getAccentColor(isDark), const Color(0xFFFF8E53)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      );

  static ThemeData get lightTheme => ThemeData(
        useMaterial3: true,
        colorScheme: lightColorScheme,
        scaffoldBackgroundColor: lightColorScheme.background,
        cardColor: lightColorScheme.surfaceVariant,
        cardTheme: CardThemeData(
          color: lightColorScheme.surfaceVariant,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(
              color: lightColorScheme.outlineVariant,
              width: 1,
            ),
          ),
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: lightColorScheme.surface,
          foregroundColor: lightColorScheme.onSurface,
          elevation: 0,
        ),
        floatingActionButtonTheme: FloatingActionButtonThemeData(
          backgroundColor: lightColorScheme.primary,
          foregroundColor: lightColorScheme.onPrimary,
        ),
      );

  static ThemeData get darkTheme => ThemeData(
        useMaterial3: true,
        colorScheme: darkColorScheme,
        scaffoldBackgroundColor: darkColorScheme.background,
        cardColor: darkColorScheme.surfaceVariant,
        cardTheme: CardThemeData(
          color: darkColorScheme.surfaceVariant,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(
              color: darkColorScheme.outline.withOpacity(0.2),
              width: 1,
            ),
          ),
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: darkColorScheme.surface,
          foregroundColor: darkColorScheme.onSurface,
          elevation: 0,
        ),
        floatingActionButtonTheme: FloatingActionButtonThemeData(
          backgroundColor: darkColorScheme.primary,
          foregroundColor: darkColorScheme.onPrimary,
        ),
      );
}

// ThemeProvider class for managing theme state
class ThemeProvider extends ChangeNotifier {
  bool _isDarkMode = false;
  bool get isDarkMode => _isDarkMode;

  ThemeProvider() {
    _loadTheme();
  }

  Future<void> _loadTheme() async {
    final prefs = await SharedPreferences.getInstance();
    _isDarkMode = prefs.getBool('isDarkMode') ?? false;
    notifyListeners();
  }

  Future<void> toggleTheme() async {
    _isDarkMode = !_isDarkMode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isDarkMode', _isDarkMode);
    notifyListeners();
  }

  ThemeData get theme => _isDarkMode ? AppTheme.darkTheme : AppTheme.lightTheme;
}
