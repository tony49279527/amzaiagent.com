from blog_curation import curate_posts, extract_posts_from_blog_js, write_blog_js


def main():
    posts = extract_posts_from_blog_js()
    curated = curate_posts(posts)
    write_blog_js(curated)
    print(f"Curated blog_posts.js from {len(posts)} to {len(curated)} posts.")


if __name__ == "__main__":
    main()
