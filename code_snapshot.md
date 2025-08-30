# Code Snapshot

## ZDownloadManager/tests/__init__.py

## ZDownloadManager/tests/test_cli.py
- class CLITests
  - test_version_flag(self)
  - test_show_config(self)
  - test_show_snapshots(self)
  - test_verify_snapshots(self)
  - test_list_models(self)
  - test_dependency_queries(self)

## ZDownloadManager/tests/test_code_scanner.py
- test_code_scanner_generates_summary(tmp_path)

## ZDownloadManager/tests/test_config.py
- class ConfigTests
  - test_update_and_reload(self)

## ZDownloadManager/tests/test_context_snapshot.py
- class ContextSnapshotTest
  - test_snapshot_created(self)

## ZDownloadManager/tests/test_downloader.py
- class DownloaderTests
  - test_download_example(self)

## ZDownloadManager/tests/test_github_adapter.py
- class GitHubAdapterTests
  - test_get_repo_info(self)
  - test_list_open_issues(self)
  - test_list_open_pull_requests(self)
  - test_list_languages(self)

## ZDownloadManager/tests/test_library_cli.py
- setup_home(tmp_path)
- test_library_scan_and_search(tmp_path)
- test_cli_list_and_search(tmp_path)
- test_cli_library_stats(tmp_path)

## ZDownloadManager/tests/test_openrouter_models.py
- class OpenRouterModelsTest
  - test_models_fetch(self)

## ZDownloadManager/tests/test_organizer.py
- class OrganizerTests
  - test_normalize_filename(self)

## ZDownloadManager/tests/test_suggestions_cache.py
- class SuggestionCacheTest
  - test_cache_reuse_without_key(self)
  - test_cli_show_cache(self)
  - test_custom_model(self)
  - test_cli_custom_model(self)
  - test_cli_custom_params(self)
  - test_streaming(self)
  - test_cli_stream(self)

## ZDownloadManager/tests/test_webscraper.py
- class WebScraperTests
  - test_example_com(self)

## ZDownloadManager/zdownloadmanager/__init__.py

## ZDownloadManager/zdownloadmanager/cli.py
- main(argv)

## ZDownloadManager/zdownloadmanager/core/config.py
- _platform_config_dir()
- class Config
  - __init__(self, path)
  - load(self)
  - save(self)
  - piece_size(self)
  - concurrency(self)
  - library_roots(self)
  - categories(self)
  - actions(self)
  - custom_openers(self)
  - suggestions_enabled(self)
  - openrouter_api_key(self)
  - openrouter_model(self)
  - openrouter_temperature(self)
  - openrouter_max_tokens(self)
  - openrouter_top_p(self)
  - last_version(self)
  - cache_dir(self)
  - update(self, **kwargs)

## ZDownloadManager/zdownloadmanager/core/downloader.py
- class Piece
- class DownloadError
- class SegmentedDownloader
  - __init__(self, urls, dest, piece_size, concurrency, timeout, user_agent)
  - _init_db(self)
  - _get_meta(self, key)
  - _set_meta(self, key, value)
  - _enumerate_pieces(self, file_size)
  - _load_pieces(self)
  - _save_piece(self, piece)
  - _probe_server(self, url)
  - download(self)
  - _sequential_download(self, file_size)

## ZDownloadManager/zdownloadmanager/core/github_adapter.py
- class GitHubAdapter
  - __init__(self, token)
  - get_repo_info(self, full_name)
  - commit_file(self, repo_full_name, path, content, message, branch)
  - create_pull_request(self, repo_full_name, title, body, head, base)
  - list_open_issues(self, repo_full_name, limit)
  - list_open_pull_requests(self, repo_full_name, limit)
  - list_languages(self, repo_full_name)

## ZDownloadManager/zdownloadmanager/core/library.py
- class Library
  - __init__(self, config)
  - _load_tags(self)
  - _save_tags(self)
  - scan(self)
  - search(self, query)
  - stats(self)
  - set_tags(self, path, tags)
  - add_tag(self, path, tag)
  - remove_tag(self, path, tag)

## ZDownloadManager/zdownloadmanager/core/organizer.py
- class Organizer
  - __init__(self, config)
  - normalize_filename(self, filename)
  - determine_category(self, filename)
  - organise(self, path)

## ZDownloadManager/zdownloadmanager/core/suggestions.py
- _cache_file(config)
- read_cache(config)
- clear_cache(config)
- get_suggestion(config, question, model)
- stream_suggestion(config, question, model)

## ZDownloadManager/zdownloadmanager/core/webscraper.py
- _get_session()
- scrape_page(url, headings, images, meta, summary, links, timeout)
- scrape_links(url, timeout)
- scrape_site(url, depth, headings, images, meta, summary, links, timeout, parallel, max_workers)
- class _SimpleHTMLParser
  - __init__(self)
  - handle_starttag(self, tag, attrs)
  - handle_endtag(self, tag)
  - handle_data(self, data)

## ZDownloadManager/zdownloadmanager/integration/native_messaging_host.py
- read_message()
- write_message(msg)
- main()

## ZDownloadManager/zdownloadmanager/integration/protocol_handler.py
- main(argv)

## ZDownloadManager/zdownloadmanager/ui/actions_editor.py
- class ActionsEditor
  - __init__(self, config, parent)
  - save(self)

## ZDownloadManager/zdownloadmanager/ui/main_window.py
- main()
- class DownloadWorker
  - __init__(self, urls, dest, cfg)
  - run(self)
- class MainWindow
  - __init__(self)
  - _setup_ui(self)
  - _setup_download_tab(self)
  - _setup_library_tab(self)
  - reload_config(self)
  - edit_actions(self)
  - set_piece_size(self)
  - set_concurrency(self)
  - toggle_suggestions(self, checked)
  - set_openrouter_api_key(self)
  - browse_dest(self)
  - add_download(self)
  - on_download_progress(self, item, done, total)
  - on_download_finished(self, item, new_path, error)
  - refresh_library(self)
  - on_tree_context_menu(self, pos)
  - on_tree_selection_changed(self)
  - open_file(self, path)
  - reveal_file(self, path)
  - add_tag_dialog(self, path)
  - run_action(self, path, cmd_template)
  - run_custom_opener(self, path, opener)
  - rename_file(self, path)
  - delete_file(self, path)
  - choose_library_root(self)

## scripts/code_scan.py
- format_args(args)
- scan_file(path)
- generate_summary(root)
- build_markdown(summary)
- main()

## scripts/context_snapshot.py
- build_dependency_map()
- generate_snapshot()
- main()

## scripts/github_tools.py
- main()

## scripts/llm_suggest.py
- main()

## scripts/openrouter_models.py
- main()
