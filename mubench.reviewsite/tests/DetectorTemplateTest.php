<?php

use Facebook\WebDriver\WebDriverBy;

require_once 'WebDriverTestCase.php';

class DetectorTemplateTest extends WebDriverTestCase
{

    public function setUp()
    {
        parent::setUp();
        $this->getRoute("/experiments/1/detectors/TestDetector/runs");
    }

    public function testAssertExperimentHeadline()
    {
        $this->getRoute("/experiments/1/detectors/TestDetector/runs");
        $headline = $this->driver->findElement(
            WebDriverBy::tagName('h1')
        );
        self::assertEquals("Experiment 1: Recall Upper Bound", $headline->getText());
    }

    public function testAssertVisibleTags()
    {
        $misuseTags = $this->driver->findElements(
            WebDriverBy::tagName("div")::className("misuse-tag")
        );
        self::assertEquals(2, count($misuseTags));
        self::assertFalse($misuseTags[0]->isDisplayed());
        $tag = $misuseTags[1]->findElement(WebDriverBy::tagName("span"));
        self::assertEquals("test-dataset2", $tag->getText());
    }

    public function testShowReviewModal()
    {
        $commentIcon = $this->driver->findElement(
            WebDriverBy::tagName("i")::className("fa-comments-o")
        );
        $modal = $this->driver->findElement(
            WebDriverBy::tagName("div")::className("modal-content")
        );
        self::assertFalse($modal->isDisplayed());
        $commentIcon->click();
        self::assertTrue($modal->isDisplayed());
    }

    public function testOpenFirstMisuseReview()
    {
        $viewLinks = $this->driver->findElements(
            WebDriverBy::cssSelector("td > a.button")
        );
        self::assertEquals(2, count($viewLinks));
        $viewLinks[0]->click();
        $this->assertRoute("/experiments/1/detectors/TestDetector/projects/mubench/versions/42/misuses/1");
    }

}
