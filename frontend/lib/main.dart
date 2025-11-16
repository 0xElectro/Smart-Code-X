import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:smat_code_x/screens/home_screen.dart';
import 'package:smat_code_x/theme/app_theme.dart';

void main() {
  runApp(const SmatCodeXApp());
}

class SmatCodeXApp extends StatelessWidget {
  const SmatCodeXApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => ThemeProvider(),
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, _) {
          return MaterialApp(
            title: 'SmatCodeX',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme.copyWith(
              textTheme: GoogleFonts.jetBrainsMonoTextTheme(
                AppTheme.lightTheme.textTheme,
              ),
            ),
            darkTheme: AppTheme.darkTheme.copyWith(
              textTheme: GoogleFonts.jetBrainsMonoTextTheme(
                AppTheme.darkTheme.textTheme,
              ),
            ),
            themeMode:
                themeProvider.isDarkMode ? ThemeMode.dark : ThemeMode.light,
            home: const HomeScreen(),
          );
        },
      ),
    );
  }
}
