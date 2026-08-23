<?php
/**
 * Plugin Name: Open Source Neuro — Spikeling Emulator
 * Description: Conditionally loads the scientific Spikeling neuronal emulator through a single isolated shortcode.
 * Version: 0.1.0
 * Requires at least: 6.2
 * Requires PHP: 7.4
 * Author: Open Source Neuro
 * License: GPL-3.0-or-later
 * License URI: https://www.gnu.org/licenses/gpl-3.0.html
 * Text Domain: osn-spikeling-emulator
 */

// SPDX-License-Identifier: GPL-3.0-or-later

defined( 'ABSPATH' ) || exit;

final class OSN_Spikeling_Emulator {
	private const SHORTCODE     = 'osn_spikeling_emulator';
	private const SCRIPT_HANDLE = 'osn-spikeling-emulator';
	private const STYLE_HANDLE  = 'osn-spikeling-emulator';
	private const MAX_SAMPLES   = 1000000;

	private static $manifest = null;

	/** Register no global styles, admin pages, options, REST endpoints or tracking. */
	public static function boot(): void {
		add_shortcode( self::SHORTCODE, array( self::class, 'render_shortcode' ) );
		add_action( 'wp_enqueue_scripts', array( self::class, 'maybe_enqueue' ), 20 );
		add_filter( 'script_loader_tag', array( self::class, 'module_script_tag' ), 10, 3 );
	}

	/** Load assets only when the current singular page actually contains this shortcode. */
	public static function maybe_enqueue(): void {
		if ( ! is_singular() ) {
			return;
		}

		$post = get_post();
		if ( ! $post instanceof WP_Post ) {
			return;
		}

		$found = has_shortcode( (string) $post->post_content, self::SHORTCODE );
		if ( ! $found ) {
			$elementor = get_post_meta( $post->ID, '_elementor_data', true );
			$found     = is_string( $elementor ) && false !== strpos( $elementor, '[' . self::SHORTCODE );
		}

		if ( ! $found ) {
			return;
		}

		self::enqueue_assets();
	}

	/** Shortcode fallback also supports dynamically rendered Elementor shortcodes. */
	public static function render_shortcode( $attributes = array() ): string {
		if ( ! self::enqueue_assets() ) {
			return '<p class="osn-spikeling-emulator__error" role="alert">'
				. esc_html__( 'The Spikeling emulator assets are currently unavailable.', 'osn-spikeling-emulator' )
				. '</p>';
		}

		$attributes = shortcode_atts(
			array(
				'speed'       => '2',
				'seed'        => '123456',
				'max_samples' => '250000',
			),
			(array) $attributes,
			self::SHORTCODE
		);

		$speed = self::bounded_integer( $attributes['speed'], 2, 0, 9 );
		$seed  = self::bounded_integer( $attributes['seed'], 123456, 1, 4294967295 );
		$limit = self::bounded_integer( $attributes['max_samples'], 250000, 1, self::MAX_SAMPLES );
		$id    = wp_unique_id( 'osn-spikeling-emulator-' );

		return sprintf(
			'<div id="%1$s" class="osn-spikeling-emulator" data-spikeling-emulator="1"'
			. ' data-spikeling-speed="%2$s" data-spikeling-seed="%3$s" data-spikeling-max-samples="%4$s"'
			. ' aria-label="%5$s"><noscript>%6$s</noscript></div>',
			esc_attr( $id ),
			esc_attr( (string) $speed ),
			esc_attr( (string) $seed ),
			esc_attr( (string) $limit ),
			esc_attr__( 'Interactive Spikeling neuronal emulator', 'osn-spikeling-emulator' ),
			esc_html__( 'The interactive neuronal emulator requires JavaScript.', 'osn-spikeling-emulator' )
		);
	}

	/** Preserve all unrelated WordPress and Elementor script tags exactly. */
	public static function module_script_tag( string $tag, string $handle, string $source ): string {
		if ( self::SCRIPT_HANDLE !== $handle ) {
			return $tag;
		}

		return sprintf( '<script type="module" src="%s" id="%s-js"></script>' . "\n", esc_url( $source ), esc_attr( $handle ) );
	}

	private static function enqueue_assets(): bool {
		$manifest = self::manifest();
		if ( null === $manifest ) {
			return false;
		}

		$root    = plugin_dir_path( __FILE__ ) . 'assets/';
		$version = (string) $manifest['version'];
		$app     = self::asset_filename( $manifest['application'], 'js' );
		$worker  = self::asset_filename( $manifest['worker'], 'js' );
		$style   = self::asset_filename( $manifest['stylesheet'], 'css' );
		if ( null === $app || null === $worker || null === $style
			|| ! is_file( $root . $app ) || ! is_file( $root . $worker ) || ! is_file( $root . $style ) ) {
			return false;
		}

		wp_enqueue_style( self::STYLE_HANDLE, plugins_url( 'assets/' . $style, __FILE__ ), array(), $version );
		wp_enqueue_script( self::SCRIPT_HANDLE, plugins_url( 'assets/' . $app, __FILE__ ), array(), $version, true );
		return true;
	}

	private static function manifest(): ?array {
		if ( null !== self::$manifest ) {
			return self::$manifest;
		}

		$file = plugin_dir_path( __FILE__ ) . 'assets/manifest.json';
		if ( ! is_readable( $file ) ) {
			return null;
		}

		$manifest = json_decode( (string) file_get_contents( $file ), true );
		if ( ! is_array( $manifest ) || ! isset( $manifest['version'], $manifest['application'], $manifest['worker'], $manifest['stylesheet'] )
			|| ! is_string( $manifest['version'] ) || ! preg_match( '/\A[a-f0-9]{16}\z/', $manifest['version'] ) ) {
			return null;
		}

		self::$manifest = $manifest;
		return self::$manifest;
	}

	private static function asset_filename( $asset, string $extension ): ?string {
		if ( ! is_array( $asset ) || ! isset( $asset['file'] ) || ! is_string( $asset['file'] ) ) {
			return null;
		}

		$pattern = '/\Aspikeling-(?:emulator|worker)\.[a-f0-9]{12}\.' . preg_quote( $extension, '/' ) . '\z/';
		return preg_match( $pattern, $asset['file'] ) ? $asset['file'] : null;
	}

	private static function bounded_integer( $value, int $fallback, int $minimum, int $maximum ): int {
		if ( ! is_scalar( $value ) || ! preg_match( '/\A\d+\z/', (string) $value ) ) {
			return $fallback;
		}

		$number = filter_var( $value, FILTER_VALIDATE_INT );
		if ( false === $number || $number < $minimum || $number > $maximum ) {
			return $fallback;
		}

		return (int) $number;
	}
}

OSN_Spikeling_Emulator::boot();
