<?php

namespace MuBench\ReviewSite\Controllers;


use MuBench\ReviewSite\Models\Misuse;
use MuBench\ReviewSite\Models\Snippet;
use Slim\Http\Request;
use Slim\Http\Response;

class SnippetsController extends Controller
{

    public function postSnippet(Request $request, Response $response, array $args)
    {
        $form = $request->getParsedBody();
        $projectId = $args['project_muid'];
        $versionId = $args['version_muid'];
        $misuseId = $args['misuse_muid'];
        $code = $form['snippet'];
        $line = $form['line'];
        $misuse = Misuse::find($form['misuse_id']);
        self::createSnippet($projectId, $versionId, $code, $line, $misuse->getFile());
        return $response->withRedirect("{$this->site_base_url}{$form['path']}");
    }

    public function deleteSnippet(Request $request, Response $response, array $args)
    {
        $form = $request->getParsedBody();
        $snippetId = $args['snippet_id'];

        Snippet::find($snippetId)->delete();

        return $response->withRedirect("{$this->site_base_url}{$form['path']}");
    }

    static function createSnippet($projectId, $versionId, $code, $line, $file)
    {
        $snippet = Snippet::firstOrNew(['project_muid' => $projectId, 'version_muid' => $versionId, 'line' => $line, 'file' => $file]);
        $snippet->snippet = $code;
        $snippet->save();
    }
}
