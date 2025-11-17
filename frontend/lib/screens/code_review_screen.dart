import 'package:flutter/material.dart';
import 'package:flutter_highlight/flutter_highlight.dart';
import 'package:flutter_highlight/themes/atom-one-dark.dart';
import 'package:provider/provider.dart';
import 'package:smat_code_x/theme/app_theme.dart';
import 'package:smat_code_x/widgets/animated_gradient_button.dart';
import 'package:smat_code_x/widgets/code_issue_card.dart';
import 'package:glassmorphism/glassmorphism.dart';
import 'package:flutter_animate/flutter_animate.dart';

class CodeReviewScreen extends StatefulWidget {
  const CodeReviewScreen({super.key});

  @override
  State<CodeReviewScreen> createState() => _CodeReviewScreenState();
}

class _CodeReviewScreenState extends State<CodeReviewScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isAnalyzing = false;
  bool _hasResults = false;

  final String _sampleCode = '''
import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: MyHomePage(title: 'Flutter Demo Home Page'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({Key key, this.title}) : super(key: key);
  
  final String title;

  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int counter = 0;
  
  void incrementCounter() {
    setState(() {
      counter++;
    });
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text(
              'You have pushed the button this many times:',
            ),
            Text(
              '\$counter',
              style: Theme.of(context).textTheme.headline4,
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: incrementCounter,
        tooltip: 'Increment',
        child: Icon(Icons.add),
      ),
    );
  }
}
''';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _startAnalysis() {
    setState(() {
      _isAnalyzing = true;
    });

    // Simulate analysis
    Future.delayed(const Duration(seconds: 3), () {
      setState(() {
        _isAnalyzing = false;
        _hasResults = true;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: colorScheme.background,
      appBar: AppBar(
        backgroundColor: colorScheme.surface,
        title: const Text('Code Review'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {},
          ),
        ],
        bottom: _hasResults
            ? TabBar(
                controller: _tabController,
                indicatorColor: colorScheme.primary,
                tabs: const [
                  Tab(text: 'Issues'),
                  Tab(text: 'Suggestions'),
                  Tab(text: 'Code'),
                ],
              )
            : null,
      ),
      body: _hasResults ? _buildResultsView(context) : _buildUploadView(context),
    );
  }

  Widget _buildUploadView(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.code,
              size: 80,
              color: colorScheme.primary.withOpacity(0.7),
            ).animate().scale(duration: 600.ms, curve: Curves.elasticOut),
            const SizedBox(height: 24),
            const Text(
              'Upload Your Code',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'Paste your code or upload a file to start the review process',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 32),
            Container(
              decoration: BoxDecoration(
                color: colorScheme.surfaceVariant,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: colorScheme.primary.withOpacity(0.3),
                  width: 1,
                ),
              ),
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: TextField(
                      maxLines: 10,
                      decoration: InputDecoration(
                        hintText: 'Paste your code here...',
                        border: InputBorder.none,
                        hintStyle: TextStyle(color: Colors.grey.shade600),
                      ),
                      style: const TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 14,
                      ),
                    ),
                  ),
                  Divider(color: Colors.grey.shade800),
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Row(
                      children: [
                        const Icon(Icons.info_outline,
                            size: 16, color: Colors.grey),
                        const SizedBox(width: 8),
                        const Text(
                          'Supports multiple languages',
                          style: TextStyle(color: Colors.grey, fontSize: 12),
                        ),
                        const Spacer(),
                        TextButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.upload_file, size: 16),
                          label: const Text('Upload File'),
                          style: TextButton.styleFrom(
                            foregroundColor: colorScheme.secondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ).animate().fadeIn(duration: 600.ms).slideY(begin: 0.2, end: 0),
            const SizedBox(height: 32),
            _isAnalyzing
                ? Column(
                    children: [
                      CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(
                            colorScheme.primary),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Analyzing your code...',
                        style: TextStyle(color: colorScheme.onSurface.withOpacity(0.6)),
                      ),
                    ],
                  ).animate().fadeIn(duration: 300.ms)
                : Consumer<ThemeProvider>(
                    builder: (context, themeProvider, _) {
                      return AnimatedGradientButton(
                        onPressed: _startAnalysis,
                        text: 'Start Review',
                        gradient: AppTheme.getPrimaryGradient(themeProvider.isDarkMode),
                        width: 200,
                      );
                    },
                  )
                    .animate()
                    .fadeIn(duration: 600.ms)
                    .slideY(begin: 0.2, end: 0),
          ],
        ),
      ),
    );
  }

  Widget _buildResultsView(BuildContext context) {
    return TabBarView(
      controller: _tabController,
      children: [
        _buildIssuesTab(context),
        _buildSuggestionsTab(context),
        _buildCodeTab(context),
      ],
    );
  }

  Widget _buildIssuesTab(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildSummaryCard(context),
        const SizedBox(height: 24),
        const Text(
          'Issues Found (3)',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        CodeIssueCard(
          title: 'Deprecated API Usage',
          description:
              'Key parameter is deprecated in StatefulWidget constructor',
          severity: 'Medium',
          location: 'MyHomePage (line 21)',
          recommendation:
              'Use key instead of Key key in constructor parameters',
          onTap: () {},
        )
            .animate()
            .fadeIn(duration: 400.ms, delay: 100.ms)
            .slideY(begin: 0.1, end: 0),
        const SizedBox(height: 16),
        CodeIssueCard(
          title: 'String Interpolation Error',
          description: 'Incorrect string interpolation syntax',
          severity: 'High',
          location: '_MyHomePageState (line 45)',
          recommendation:
              'Use \${counter} instead of \$counter for string interpolation',
          onTap: () {},
        )
            .animate()
            .fadeIn(duration: 400.ms, delay: 200.ms)
            .slideY(begin: 0.1, end: 0),
        const SizedBox(height: 16),
        CodeIssueCard(
          title: 'Missing Required Annotation',
          description: 'Missing @override annotation',
          severity: 'Low',
          location: 'MyApp (line 8)',
          recommendation: 'Add @override annotation before Widget build method',
          onTap: () {},
        )
            .animate()
            .fadeIn(duration: 400.ms, delay: 300.ms)
            .slideY(begin: 0.1, end: 0),
      ],
    );
  }

  Widget _buildSuggestionsTab(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'Suggestions (2)',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        CodeIssueCard(
          title: 'Use const Constructor',
          description: 'Consider using const constructor for immutable widgets',
          severity: 'Suggestion',
          location: 'Multiple locations',
          recommendation:
              'Add const keyword to widget constructors where possible',
          onTap: () {},
        )
            .animate()
            .fadeIn(duration: 400.ms, delay: 100.ms)
            .slideY(begin: 0.1, end: 0),
        const SizedBox(height: 16),
        CodeIssueCard(
          title: 'Extract Widget Method',
          description: 'Consider extracting complex widget trees into methods',
          severity: 'Suggestion',
          location: '_MyHomePageState.build',
          recommendation:
              'Extract the Column widget into a separate method for better readability',
          onTap: () {},
        )
            .animate()
            .fadeIn(duration: 400.ms, delay: 200.ms)
            .slideY(begin: 0.1, end: 0),
      ],
    );
  }

  Widget _buildCodeTab(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 10,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: HighlightView(
                _sampleCode,
                language: 'dart',
                theme: atomOneDarkTheme,
                padding: const EdgeInsets.all(16),
                textStyle: const TextStyle(
                  fontFamily: 'JetBrains Mono',
                  fontSize: 14,
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.copy),
                label: const Text('Copy Code'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: colorScheme.surfaceVariant,
                  foregroundColor: colorScheme.onSurfaceVariant,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
              ),
              const SizedBox(width: 16),
              ElevatedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.download),
                label: const Text('Download Fixed'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: colorScheme.primary,
                  foregroundColor: colorScheme.onPrimary,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return GlassmorphicContainer(
      width: double.infinity,
      height: 180,
      borderRadius: 20,
      blur: 20,
      alignment: Alignment.center,
      border: 2,
      linearGradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          Colors.white.withOpacity(0.1),
          Colors.white.withOpacity(0.05),
        ],
      ),
      borderGradient: LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [
          colorScheme.primary.withOpacity(0.5),
          colorScheme.secondary.withOpacity(0.5),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    'Code Review Summary',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      _buildSummaryItem(
                        icon: Icons.error_outline,
                        color: Colors.red,
                        count: '1',
                        label: 'Critical',
                      ),
                      const SizedBox(width: 16),
                      _buildSummaryItem(
                        icon: Icons.warning_amber_outlined,
                        color: Colors.orange,
                        count: '2',
                        label: 'Warnings',
                      ),
                      const SizedBox(width: 16),
                      _buildSummaryItem(
                        icon: Icons.lightbulb_outline,
                        color: Colors.blue,
                        count: '2',
                        label: 'Suggestions',
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Code Quality Score: 78/100',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [
                    colorScheme.primary.withOpacity(0.7),
                    colorScheme.secondary.withOpacity(0.7),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              child: const Center(
                child: Text(
                  '78%',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 600.ms).scale(begin: const Offset(0.95, 0.95));
  }

  Widget _buildSummaryItem({
    required IconData icon,
    required Color color,
    required String count,
    required String label,
  }) {
    return Expanded(
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              icon,
              color: color,
              size: 20,
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                count,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
